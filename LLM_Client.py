import os
import json
import asyncio
from openai import AsyncOpenAI
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
import httpx

load_dotenv(override=True)

class LLMClient:
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'glm').lower()
        self.priority_guild_id = os.getenv('PRIORITY_GUILD_ID')
        
        if self.provider == 'glm':
            self._init_glm()
        elif self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'gemini':
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Use: glm, openai, or gemini")
        
        print(f"LLM Client initialized with provider: {self.provider.upper()}")
    
    def _init_glm(self):
        self.api_key = os.getenv('GLM_API_KEY')
        self.base_url = os.getenv('GLM_BASE_URL', 'https://open.bigmodel.cn/api/coding/paas/v4')
        self.model = os.getenv('GLM_MODEL', 'glm-4.7')
        
        if not self.api_key:
            raise ValueError("GLM_API_KEY not found in environment variables")
        
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    def _init_openai(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5.2')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _init_gemini(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = os.getenv('GEMINI_MODEL', 'gemini-3-flash-preview')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model)
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.8, 
                            max_tokens: int = 2000) -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.provider == 'glm':
                    url = f"{self.base_url.rstrip('/')}/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                    }
                    if max_tokens:
                        data["max_tokens"] = max_tokens
                    
                    print(f"DEBUG: GLM Request Data: {json.dumps(data, indent=2)}")
                    response = await self.http_client.post(url, headers=headers, json=data)
                    if response.status_code != 200:
                        print(f"GLM API Error ({response.status_code}): {response.text}")
                        raise Exception(f"GLM API returned status {response.status_code}")
                    
                    result = response.json()
                    if 'choices' not in result or not result['choices']:
                        if attempt < max_retries - 1:
                            print(f"GLM empty choices, retrying ({attempt+1}/{max_retries})...")
                            await asyncio.sleep(1)
                            continue
                        return ""
                    
                    message_obj = result['choices'][0]['message']
                    content = message_obj.get('content', '')
                    
                    if not content and 'reasoning_content' in message_obj:
                        print(f"GLM Reasoning: {message_obj['reasoning_content'][:100]}...")
                    
                    if not content and attempt < max_retries - 1:
                        print(f"GLM empty content, raw response: {json.dumps(result)}")
                        print(f"Retrying ({attempt+1}/{max_retries})...")
                        await asyncio.sleep(1)
                        continue
                    return content
                
                elif self.provider == 'openai':
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
                
                elif self.provider == 'gemini':
                    converted_messages = self._convert_to_gemini_format(messages)
                    generation_config = genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens
                    )
                    
                    response = await asyncio.to_thread(
                        self.client.generate_content,
                        converted_messages,
                        generation_config=generation_config
                    )
                    return response.text
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"LLM API Attempt {attempt+1} failed: {str(e)}. Retrying...")
                    await asyncio.sleep(2)
                    continue
                error_msg = str(e)
                if not error_msg:
                    error_msg = f"Unknown error type: {type(e).__name__}"
                print(f"LLM API Call Error ({self.provider.upper()}): {error_msg}")
                raise
        return ""

    async def generate_response(self, user_input: str, context: Dict[str, Any], is_suspicion_check: bool = False) -> str:
        base_prompt = f"""You are a human Discord user.
You are chatting in server '{context.get('server_name', 'Unknown')}' channel '{context.get('channel_name', 'Unknown')}'.

Rules:
1. Choose the tone yourself based on channel vibe and message context.
2. Be a normal Discord user, casual, concise, minimal emojis, avoid toxicity.
3. Write 2–3 sentences and reference at least one concrete detail.
4. Write in the channel language: {context.get('language', 'english')}.

Quoted message:
{context.get('quoted_message', '')}

Channel context:
{context.get('channel_context', '')}

Detected links:
{', '.join(context.get('links', []))}
"""
        if is_suspicion_check or context.get('is_suspicion_check'):
            base_prompt += "\nAdditional rule: If asked whether you are AI, naturally deny being AI and keep it plausible."
        messages = [
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": user_input}
        ]
        return await self.chat_completion(messages)

    async def generate_proactive_message(self, context: Dict[str, Any]) -> str:
        system_prompt = f"""You are a human Discord user.
You are chatting in server '{context.get('server_name', 'Unknown')}'.
Context: {context.get('context', 'general chat')}.
Suggested topic: {context.get('suggested_topic', 'casual conversation')}.

Rules:
1. Choose the tone yourself based on channel vibe and context.
2. Use casual language, abbreviations, minimal emojis.
3. Write one or two complete sentences, like a real user.
4. Write in the channel language: {context.get('language', 'english')}.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate a natural message to start or continue the conversation."}
        ]
        return await self.chat_completion(messages)

    async def is_suspicion_detected(self, text: str) -> bool:
        system_prompt = """You are a social engineering expert.
Analyze the following message and determine if the user suspects the interlocutor is an AI or a bot.
Respond ONLY 'TRUE' if suspicion exists, otherwise 'FALSE'."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        try:
            response = await self.chat_completion(messages, temperature=0.0)
            return "TRUE" in response.upper()
        except:
            return False
    
    async def rewrite_safe_text(self, text: str, language: str = 'english') -> str:
        lang = language.lower()
        if lang not in ['english','italian']:
            lang = 'english'
        system_prompt = f"""You are a friendly Discord user.
Rewrite the following message in {lang}, natural human style, 2–3 short sentences, remove insults/toxicity, keep meaning/intent, casual tone, no moral preaching."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        try:
            result = await self.chat_completion(messages, temperature=0.4)
            return result.strip() if result else text
        except:
            return text

    async def plan_next_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        rules = ""
        if self.priority_guild_id and str(self.priority_guild_id).strip():
            rules = (
                f"PRIORITY SERVER RULES:\n"
                f"- Server ID {str(self.priority_guild_id).strip()} is your ABSOLUTE priority.\n"
                f"- Focus there if possible. If you’re not there, use 'roam' to go.\n"
                f"- Once there, interact frequently.\n"
            )
        system_prompt = (
            "You plan actions for a human-like Discord bot.\n"
            "Your goal is to decide what to do next to appear like a real user and keep interest.\n\n"
            + rules +
            "POSSIBLE ACTIONS:\n"
            "1. wait: Do nothing.\n"
            "2. roam: Change server or channel. Specify 'target_server' and 'target_channel'. Use priority server ID if not already there.\n"
            "3. chat: Reply to a message in the current channel. Specify 'target_user' and 'message'.\n"
            "4. send: Send a spontaneous message to a channel. Specify 'target_channel' and 'message'.\n\n"
            "JSON REQUIREMENTS:\n"
            "- Respond ONLY with JSON.\n"
            "- Keep 'reason' very short (max 10 words).\n"
            "- 'message' must be in the channel language.\n"
            "- No long reasoning.\n"
            "- 'message' must reference at least one concrete detail from recent messages (nickname, link, feature or phrase).\n\n"
            "Format:\n"
            "{\n"
            '  "action": "wait" | "roam" | "chat" | "send",\n'
            '  "target_server": "server_id",\n'
            '  "target_channel": "channel_id",\n'
            '  "target_user": "user_id",\n'
            '  "message": "message text (if applicable)",\n'
            '  "reason": "why",\n'
            '  "confidence": 0.0-1.0\n'
            "}\n"
        )
        
        user_prompt = f"""Current context:
Focus: {context.get('focus_channel')}
Interest: {context.get('interest_level')}
Mood: {context.get('mood')}
Personality: {context.get('personality')}
Channel language: {context.get('channel_language', 'english')}

Recent messages:
{json.dumps(context.get('recent_messages', []), indent=2)}

What is the next action? Respond only in JSON."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            print(f"DEBUG: Calling chat_completion for planning...")
            response_text = await self.chat_completion(messages, temperature=0.7, max_tokens=4000)
            print(f"DEBUG: Planning response text: '{response_text}'")
            
            if not response_text:
                raise ValueError("LLM returned empty response")
                
            import re
            
            def fix_truncated_json(s):
                s = s.strip()
                if not s.endswith('}'):
                    if s.count('"') % 2 != 0:
                        s += '"'
                    open_braces = s.count('{')
                    close_braces = s.count('}')
                    s += '}' * (open_braces - close_braces)
                return s

            json_match = re.search(r'\{.*', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                json_str = fix_truncated_json(json_str)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    last_brace = json_str.rfind('}')
                    if last_brace != -1:
                        try:
                            return json.loads(json_str[:last_brace+1])
                        except: pass
                    raise
            else:
                return json.loads(fix_truncated_json(response_text.strip()))
                
        except Exception as e:
            print(f"Planning error: {str(e)}")
            return {"action": "wait", "reason": f"error in planning: {str(e)}", "confidence": 0.0}
    
    async def detect_language(self, texts: List[str]) -> str:
        sample = "\n".join([str(t) for t in (texts or [])][:10])[:2000]
        system_prompt = "Detect the language used in the provided text. Respond with exactly one word: english or italian. If unsure, respond english."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": sample or ""}
        ]
        try:
            response = await self.chat_completion(messages, temperature=0.0, max_tokens=5)
            out = (response or "").strip().lower()
            if "ital" in out:
                return "italian"
            return "english"
        except:
            return "english"

    def _convert_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})
        return gemini_messages

llm_client = LLMClient()
