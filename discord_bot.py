import discord
import asyncio
import random
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import deque
from discord.ext import commands
import os
from dotenv import load_dotenv
import uuid
import hashlib

from database import db_manager
from LLM_Client import llm_client
from safety_filter import SafetyFilter

load_dotenv(override=True)

def log_to_file(component: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{component}] {message}\n"
    try:
        with open("debug.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write to debug.txt: {e}")

log_to_file("ENV", "dotenv loaded")

class DiscordAIBot(commands.Bot):
    def __init__(self):
        log_to_file("INIT", "Initializing DiscordAIBot...")
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.messages = True
        intents.presences = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.recent_messages = deque(maxlen=50)
        self.pending_dms = deque(maxlen=20)
        self.active_channels = set()
        self.last_action = 'none'
        self.mood = 'chill'
        self.personality = 'sarcastic, direct, ironic, sometimes chaotic'
        self.conversation_history = {}
        self.action_queue = asyncio.Queue()
        
        self.current_focus_guild_id = None
        self.current_focus_channel_id = None
        self.interest_level = 0.0
        self.last_stimulus_time = datetime.now()
        self.focus_locked = False
        self.blocked_channel_ids = set([1328627097513754674])
        self.default_language = 'english'
        self.session_id = str(uuid.uuid4())
        tok = os.getenv('DISCORD_BOT_TOKEN') or ''
        self.token_fingerprint = hashlib.sha256(tok.encode()).hexdigest()[:12] if tok else None
        self.last_send_times: Dict[int, float] = {}
        self.min_send_interval_secs = 45
        raw_priority = os.getenv('PRIORITY_GUILD_ID')
        self.priority_guild_id = None
        if raw_priority:
            try:
                self.priority_guild_id = int(str(raw_priority).strip())
            except Exception:
                self.priority_guild_id = None
        
        self.safety_filter = SafetyFilter()
        
        self.last_presence_change = datetime.now()
        self.current_status = discord.Status.online
        self.possible_activities = [
            (discord.ActivityType.playing, "Visual Studio Code"),
            (discord.ActivityType.playing, "Minecraft"),
            (discord.ActivityType.listening, "Spotify"),
            (discord.ActivityType.watching, "YouTube"),
            (discord.ActivityType.playing, "Elden Ring"),
            (discord.ActivityType.listening, "lo-fi hip hop"),
            (None, None) 
        ]
        
        self.is_sleeping = False
        self.sleep_end_time = None
        
        import re
        self.url_re = re.compile(r'https?://\S+')
        
    def _update_interest(self, amount: float):
        self.interest_level = max(0.0, min(1.0, self.interest_level + amount))
        if amount > 0:
            self.last_stimulus_time = datetime.now()

    async def _update_presence(self):
        now = datetime.now()
        if (now - self.last_presence_change).total_seconds() < random.uniform(1800, 7200):
            return

        self.last_presence_change = now
        
        if self.is_sleeping:
            await self.change_presence(status=discord.Status.idle, activity=None)
            return

        status_opts = [discord.Status.online, discord.Status.idle, discord.Status.dnd]
        new_status = random.choices(status_opts, weights=[0.7, 0.2, 0.1])[0]
        
        act_type, act_name = random.choice(self.possible_activities)
        activity = discord.Activity(type=act_type, name=act_name) if act_type else None
        
        try:
            await self.change_presence(status=new_status, activity=activity)
            log_to_file("PRESENCE", f"Updated presence: {new_status} - {act_name}")
        except Exception as e:
            log_to_file("ERROR", f"Failed to update presence: {e}")

    async def _manage_focus(self):
        time_since_stimulus = (datetime.now() - self.last_stimulus_time).total_seconds()
        
        decay = 0.02
        if time_since_stimulus > 60:
            decay = 0.05
        if time_since_stimulus > 180:
            decay = 0.1
            
        self._update_interest(-decay)
        
        if self.interest_level <= 0.0:
            await self._switch_focus()

    def _human_cadence_ok(self, channel_id: int) -> bool:
        now = datetime.now().timestamp()
        last = self.last_send_times.get(channel_id, 0.0)
        jitter = random.uniform(5.0, 40.0)
        if (now - last) < (self.min_send_interval_secs + jitter):
            return False
        self.last_send_times[channel_id] = now
        return True

    async def _switch_focus(self):
        if not self.guilds:
            return
        guild = None
        if self.priority_guild_id:
            try:
                guild = self.get_guild(self.priority_guild_id)
            except Exception:
                guild = None
        if not guild:
            guild = random.choice(self.guilds)
        
        channels = [c for c in guild.text_channels if c.permissions_for(guild.me).read_messages and c.permissions_for(guild.me).send_messages]
        
        if channels:
            channel = random.choice(channels)
            self.current_focus_guild_id = guild.id
            self.current_focus_channel_id = channel.id
            self.interest_level = 0.6
            self.last_stimulus_time = datetime.now()
            print(f"Roaming: Switched focus to {guild.name} #{channel.name}")
            await db_manager.save_log('ROAMING', f'Switched focus to {guild.name} #{channel.name}')
            log_to_file("ROAMING", f"Focus guild {guild.id} {guild.name}, channel {channel.id} {channel.name}, interest {self.interest_level:.2f}")
            
            try:
                history = [msg async for msg in channel.history(limit=5)]
                if history:
                    last_msg = history[0]
                    try:
                        pass
                    except Exception:
                        pass
                
                for message in reversed(history):
                     if message.author != self.user:
                        self._add_to_recent(message)
            except Exception as e:
                print(f"Error reading history after switch: {e}")

    async def _detect_language_llm(self, texts):
        try:
            return await llm_client.detect_language(texts)
        except:
            return self.default_language

    def _build_ai_context(self, message, language):
        user_id_str = str(message.author.id)
        recent_channel = [m for m in self.recent_messages if m.get('channel') == message.channel.id][-8:]
        texts = [m['content'] for m in recent_channel]
        links = []
        for t in texts + [message.content]:
            links.extend(self.url_re.findall(t))
        links = list(dict.fromkeys(links))[:5]
        ctx_lines = []
        for m in recent_channel:
            a = m.get('author_name') or str(m.get('author'))
            c = (m.get('content') or '')[:160]
            ctx_lines.append(f"{a}: {c}")
        channel_context = "\\n".join(ctx_lines)
        topic_hint = ''
        base = (message.content or '').lower()
        if any(k in base for k in ['archgen','gemini','puter','groq','api','workflow','diagram']):
            topic_hint = 'tech_product_discussion'
        return {
            'personality': self.personality,
            'mood': self.mood,
            'conversation_context': '\\n'.join(list(self.conversation_history.get(user_id_str, []))[-5:]),
            'server_name': message.guild.name if message.guild else 'DM',
            'channel_name': message.channel.name if hasattr(message.channel, 'name') else 'DM',
            'language': language,
            'author_name': message.author.name,
            'quoted_message': message.content,
            'channel_context': channel_context,
            'links': links,
            'topic_hint': topic_hint
        }

    def _add_to_recent(self, message):
         msg_data = {
            'id': message.id,
            'author': message.author.id,
            'author_name': message.author.name,
            'content': message.content,
            'channel': message.channel.id,
            'channel_name': message.channel.name if hasattr(message.channel, 'name') else 'DM',
            'guild': message.guild.id if message.guild else None,
            'guild_name': message.guild.name if message.guild else None,
            'is_dm': isinstance(message.channel, discord.DMChannel),
            'timestamp': datetime.now().isoformat()
        }
         self.recent_messages.append(msg_data)

    async def setup_hook(self):
        log_to_file("SETUP", "Running setup_hook")
        await db_manager.initialize()
        await db_manager.save_log('STARTUP', 'Discord AI Bot started')
        print("Discord AI Bot started successfully!")
    
    async def on_ready(self):
        log_to_file("READY", f"Logged in as {self.user} ({self.user.id})")
        print(f'{self.user} is online!')
        print(f'Connected to {len(self.guilds)} servers')
        if self.token_fingerprint:
            log_to_file("AUTH", f"Session {self.session_id} TokenFP {self.token_fingerprint}")
        
        for guild in self.guilds:
            log_to_file("READY", f"Connected to guild: {guild.name} ({guild.id})")
            await db_manager.save_log(
                'SERVER_JOIN',
                f'Connected to server: {guild.name} ({guild.id})',
                server_id=str(guild.id),
                server_name=guild.name
            )
            print(f' - {guild.name} ({guild.id})')
        
        try:
            await self.cleanup_last_bot_message(1328627097513754674)
            log_to_file("CLEANUP", "Attempted cleanup in TRAE tips-and-tricks")
        except Exception as e:
            log_to_file("CLEANUP", f"Cleanup error: {e}")
        
        asyncio.create_task(self.action_planner())
        asyncio.create_task(self.process_action_queue())
    
    async def on_guild_join(self, guild):
        log_to_file("GUILD_JOIN", f"Joined new guild: {guild.name} ({guild.id})")
        await db_manager.save_log(
            'SERVER_JOIN',
            f'Joined server: {guild.name} ({guild.id})',
            server_id=str(guild.id),
            server_name=guild.name
        )
        print(f'Joined server: {guild.name}')
    
    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        
        log_to_file("ON_MESSAGE", f"Received message from {message.author} in {message.channel}: {message.content[:50]}...")
        
        try:
            is_dm = isinstance(message.channel, discord.DMChannel)
            
            try:
                await db_manager.save_message(
                    discord_id=message.author.id,
                    username=message.author.name,
                    display_name=message.author.display_name,
                    discord_message_id=message.id,
                    channel_id=message.channel.id,
                    channel_name=message.channel.name if hasattr(message.channel, 'name') else 'DM',
                    content=message.content,
                    server_id=message.guild.id if message.guild else None,
                    server_name=message.guild.name if message.guild else None,
                    is_dm=is_dm
                )
            except Exception as e:
                print(f"Database error while saving message: {e}")
            
            is_focused_channel = (message.channel.id == self.current_focus_channel_id)
            is_mention = self.user.mentioned_in(message)
            
            if not is_focused_channel and not is_mention and not is_dm:
                log_to_file("ON_MESSAGE", "Ignored: Message not in focused channel and no mention/DM")
                return

            if is_dm:
                log_to_file("FOCUS", "Interest boosted due to DM")
                self._update_interest(0.5)
            elif is_mention:
                if message.guild:
                    self.current_focus_guild_id = message.guild.id
                    self.current_focus_channel_id = message.channel.id
                self.interest_level = 1.0
                self.last_stimulus_time = datetime.now()
                print(f"Focus switched to {message.guild.name if message.guild else 'DM'} due to mention")
                log_to_file("FOCUS", f"Focus switched to {message.guild.name if message.guild else 'DM'} due to mention")
            elif is_focused_channel:
                log_to_file("FOCUS", "Interest maintained (focused channel)")
                self._update_interest(0.1)

            self._add_to_recent(message)
            self.active_channels.add(message.channel.id)
            
            if is_dm:
                self.pending_dms.append(self.recent_messages[-1])
            
            user_id_str = str(message.author.id)
            if user_id_str not in self.conversation_history:
                self.conversation_history[user_id_str] = deque(maxlen=10)
            self.conversation_history[user_id_str].append(message.content)
            
            try:
                suspicion = await llm_client.is_suspicion_detected(message.content)
                if suspicion:
                    log_to_file("SUSPICION", f"Suspicion detected in message: {message.content}")
                    await db_manager.log_suspicion(
                        message.author.id,
                        message.author.name,
                        message.content
                    )
                    await self.handle_suspicion(message)
                else:
                    await self.action_queue.put(('handle_message', message))
            except Exception as e:
                print(f"LLM/Queue error: {e}")
                log_to_file("ERROR", f"LLM/Queue error: {e}")
                await db_manager.save_log('ERROR', f'LLM/Queue error: {str(e)}')
        
        except Exception as e:
            print(f"General message handling error: {e}")
            log_to_file("ERROR", f"General message handling error: {e}")
            await db_manager.save_log('ERROR', f'General message error: {str(e)}')
    
    async def handle_suspicion(self, message):
        log_to_file("SUSPICION_HANDLE", f"Handling suspicion for message: {message.id}")
        try:
            response = await llm_client.generate_response(
                message.content,
                {
                    'personality': self.personality,
                    'mood': self.mood,
                    'is_suspicion_check': True
                },
                is_suspicion_check=True
            )
            
            is_safe, reason = self.safety_filter.is_safe(response)
            if not is_safe:
                log_to_file("SAFETY_BLOCK", f"Blocked suspicion response: {reason}")
                response = "..."  # Fallback
            
            await message.reply(response)
            
            await db_manager.save_bot_response(
                discord_message_id=message.id,
                channel_id=message.channel.id,
                content=response,
                action_type='SUSPICION_REPLY',
                server_id=message.guild.id if message.guild else None,
                is_dm=isinstance(message.channel, discord.DMChannel)
            )
            
            await db_manager.save_log('SUSPICION_REPLY', f'Suspicion response: {response[:100]}')
        
        except Exception as e:
            print(f"Suspicion handling error: {e}")
    
    async def action_planner(self):
        log_to_file("PLANNER", "Starting action planner loop")
        while True:
            try:
                await asyncio.sleep(random.uniform(8.0, 16.0))
                
                # Check Sleep Mode
                now = datetime.now()
                if self.is_sleeping:
                    if now < self.sleep_end_time:
                        if random.random() < 0.05: 
                             log_to_file("SLEEP", "Brief wake up check...")
                        else:
                             continue 
                    else:
                        self.is_sleeping = False
                        log_to_file("SLEEP", "Waking up from sleep mode.")
                        await self._update_presence()
                else:
                    if now.hour in [1, 2, 3, 4, 5] and random.random() < 0.1:
                         sleep_duration = random.uniform(4, 8) 
                         self.sleep_end_time = now + asyncio.timedelta(hours=sleep_duration)
                         self.is_sleeping = True
                         log_to_file("SLEEP", f"Going to sleep for {sleep_duration:.2f} hours until {self.sleep_end_time}")
                         await self.change_presence(status=discord.Status.idle, activity=None)
                         continue

                await self._manage_focus()
                await self._update_presence()
                
                log_to_file("FOCUS_MANAGE", f"Current interest: {self.interest_level:.2f}, Focus: {self.current_focus_channel_id}")
                
                current_messages = [
                    m for m in self.recent_messages 
                    if m['channel'] == self.current_focus_channel_id or m['is_dm']
                ]
                
                channel_texts = [m['content'] for m in current_messages[-10:]]
                channel_language = await self._detect_language_llm(channel_texts)
                
                context = {
                    'servers': [{'id': g.id, 'name': g.name} for g in self.guilds],
                    'active_channels': list(self.active_channels),
                    'recent_messages': current_messages[-10:],
                    'pending_dms': list(self.pending_dms),
                    'mood': self.mood,
                    'last_action': self.last_action,
                    'personality': self.personality,
                    'interest_level': self.interest_level,
                    'focus_channel': self.current_focus_channel_id,
                    'channel_language': channel_language
                }
                
                try:
                    focus_name = ''
                    if self.current_focus_channel_id:
                        ch = self.get_channel(int(self.current_focus_channel_id))
                        if ch:
                            focus_name = f"{ch.guild.name if hasattr(ch,'guild') and ch.guild else ''} #{ch.name}"
                    log_to_file("PLANNER_CTX", f"Servers: {len(self.guilds)}, Focus: {self.current_focus_channel_id} {focus_name}, Lang: {channel_language}, Interest: {self.interest_level:.2f}")
                except Exception:
                    pass
                
                if self.interest_level > 0.2:
                    log_to_file("PLANNER", "Planning next action (interest sufficient)")
                    action_plan = await llm_client.plan_next_action(context)
                    log_to_file("PLANNER", f"Plan generated: {action_plan}")
                    
                    if action_plan['confidence'] > 0.6:
                        await self.action_queue.put(('execute_action', action_plan))
                else:
                    log_to_file("PLANNER", "Skipping planning (low interest)")
            
            except Exception as e:
                error_msg = str(e)
                print(f"Action planner error: {error_msg}")
                log_to_file("ERROR", f"Action planner error: {error_msg}")
                
                if "AUTH_ERROR" in error_msg:
                    print("CRITICAL: Auth error detected. Stopping planner for 5 minutes.")
                    log_to_file("CRITICAL", "Auth error. Pausing planner.")
                    await asyncio.sleep(300) # Wait 5 minutes before retrying

    
    async def process_action_queue(self):
        log_to_file("QUEUE", "Starting action queue processor")
        while True:
            try:
                action_type, data = await self.action_queue.get()
                log_to_file("QUEUE", f"Processing action: {action_type}")
                
                if action_type == 'handle_message':
                    await self.handle_ai_response(data)
                elif action_type == 'execute_action':
                    await self.execute_action(data)
            
            except Exception as e:
                print(f"Action processing error: {e}")
                log_to_file("ERROR", f"Action processing error: {e}")
    
    async def handle_ai_response(self, message):
        try:
            should_respond = await self.decide_to_respond(message)
            log_to_file("RESPONSE_DECISION", f"Should respond to {message.id}? {should_respond}")
            
            if should_respond:
                user_id_str = str(message.author.id)
                conversation_context = list(self.conversation_history.get(user_id_str, []))[-5:]
                recent_channel_texts = [m['content'] for m in self.recent_messages if m.get('channel') == message.channel.id][-10:]
                language = await self._detect_language_llm([message.content] + recent_channel_texts)
                
                if not self._human_cadence_ok(message.channel.id):
                    log_to_file("CADENCE_SKIP", f"Skip reply cadence in {message.channel.id}")
                    return
                
                await self._simulate_human_delay(len(message.content))
                
                # Mark as read (removed self-bot .ack())
                try:
                    pass
                except:
                    pass

                try:
                    log_to_file("LLM_GEN", "Generating response...")
                    ai_ctx = self._build_ai_context(message, language)
                    
                    async with message.channel.typing():
                        response = await llm_client.generate_response(message.content, ai_ctx)
                except Exception as llm_error:
                    print(f"LLM Generation Error: {llm_error}")
                    await db_manager.save_log('ERROR', f'LLM Generation error: {str(llm_error)}')
                    return

                if not response:
                    print("Empty response from LLM")
                    return
                
                try:
                    response = await llm_client.rewrite_safe_text(response, language)
                except Exception as mod_err:
                    log_to_file("MODERATE", f"Rewrite failed: {mod_err}")

                is_safe, reason = self.safety_filter.is_safe(response)
                if not is_safe:
                    log_to_file("SAFETY_BLOCK", f"Blocked response: {reason}")
                    print(f"Safety Block: {reason}")
                    return

                log_to_file("RESPONSE", f"Generated: {response}")
                print(f"Response generated: {response[:50]}...")
                
                typing_time = len(response) / random.uniform(5.0, 9.0)
                if typing_time > 0.5:
                     async with message.channel.typing():
                        await asyncio.sleep(typing_time)

                try:
                    await message.reply(response)
                    ch_name = message.channel.name if hasattr(message.channel, 'name') else 'DM'
                    log_to_file("RESPONSE", f"Replied to {message.author.name} in {ch_name}: {response}")
                except discord.Forbidden:
                    print(f"Permission denied to reply in {message.channel}")
                except discord.HTTPException as http_err:
                    print(f"HTTP error replying to message: {http_err}")
                
                try:
                    await db_manager.save_bot_response(
                        discord_message_id=message.id,
                        channel_id=message.channel.id,
                        content=response,
                        action_type='REPLY',
                        server_id=message.guild.id if message.guild else None,
                        is_dm=isinstance(message.channel, discord.DMChannel)
                    )
                    
                    user = await db_manager.get_or_create_user(
                        message.author.id,
                        message.author.name,
                        message.author.display_name,
                        message.guild.id if message.guild else None,
                        message.guild.name if message.guild else None
                    )
                    
                    await db_manager.save_interaction(
                        user_id=user.id,
                        interaction_type='RESPONSE',
                        content=f'Replied to: {message.content[:50]}...',
                        channel_id=message.channel.id,
                        server_id=message.guild.id if message.guild else None
                    )
                except Exception as db_err:
                    print(f"Database error after reply: {db_err}")
                
                self.last_action = 'REPLY'
        
        except Exception as e:
            print(f"AI response general error: {e}")
            await db_manager.save_log('ERROR', f'AI response general error: {str(e)}')
    
    async def decide_to_respond(self, message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True
        
        if self.user.mentioned_in(message):
            return True
        
        if self.interest_level > 0.5:
             chance = (self.interest_level - 0.5) * 0.8
             return random.random() < chance
        
        return False
    
    async def _simulate_human_delay(self, content_length: int):
        base_delay = random.uniform(0.5, 2.0)
        reading_time = content_length / random.uniform(15.0, 25.0)
        total_delay = base_delay + reading_time
        
        total_delay = min(total_delay, 10.0)
        
        log_to_file("DELAY", f"Simulating human delay: {total_delay:.2f}s")
        await asyncio.sleep(total_delay)

    async def execute_action(self, action_plan: Dict):
        try:
            action = action_plan.get('action')
            if not action or action.upper() == 'WAIT':
                return
                
            log_to_file("EXECUTE", f"Executing action: {action}")
            
            if action.lower() == 'roam':
                target_server = action_plan.get('target_server')
                target_channel = action_plan.get('target_channel')
                
                if target_server:
                    try:
                        self.current_focus_guild_id = int(target_server)
                        guild = self.get_guild(self.current_focus_guild_id)
                        if not target_channel or str(target_channel) == "0":
                            if guild:
                                for channel in guild.text_channels:
                                    if channel.permissions_for(guild.me).send_messages:
                                        target_channel = channel.id
                                        break
                        
                        if target_channel:
                            self.current_focus_channel_id = int(target_channel)
                            
                        self.interest_level = 0.8
                        self.last_stimulus_time = datetime.now()
                        
                        server_name = guild.name if guild else "Unknown"
                        print(f"Roaming: Switched focus to {server_name} #{target_channel}")
                        log_to_file("ROAMING", f"Switched focus to {server_name} #{target_channel}")
                    except ValueError:
                        print(f"Invalid server/channel ID in roam: {target_server}/{target_channel}")
                
            elif action.upper() == 'SEND' or action.lower() == 'chat':
                await self.send_message(action_plan)
            elif action.upper() == 'DM_SEND':
                await self.send_dm(action_plan)
            elif action.upper() == 'READ':
                await self.read_messages(action_plan)
            
            self.last_action = action
        
        except Exception as e:
            print(f"Action execution error: {e}")
            log_to_file("ERROR", f"Action execution error: {e}")
            await db_manager.save_log('ERROR', f'Action execution error: {str(e)}')
    
    async def send_message(self, action_plan: Dict):
        try:
            channel_id = action_plan.get('target_channel')
            if not channel_id:
                return
            
            channel = self.get_channel(int(channel_id))
            if not channel:
                return
            
            if int(channel_id) in self.blocked_channel_ids:
                log_to_file("BLOCK", f"Message blocked in {channel.name}")
                return
            
            if not self._human_cadence_ok(channel.id):
                log_to_file("CADENCE_SKIP", f"Skip send cadence in {channel.id}")
                return
            
            message_content = action_plan.get('message')
            if not message_content:
                context = {
                    'context': 'general chat',
                    'server_name': channel.guild.name if hasattr(channel, 'guild') else '',
                    'suggested_topic': 'casual conversation',
                    'language': await self._detect_language_llm([m['content'] for m in self.recent_messages if m.get('channel') == channel.id][-10:])
                }
                message_content = await llm_client.generate_proactive_message(context)
            else:
                target_lang = await self._detect_language_llm([m['content'] for m in self.recent_messages if m.get('channel') == channel.id][-10:])
                if target_lang == 'english':
                    if any(ch in message_content for ch in ['à','è','é','ì','ò','ù']) or ' che ' in message_content.lower():
                        context = {
                            'context': 'general chat',
                            'server_name': channel.guild.name if hasattr(channel, 'guild') else '',
                            'suggested_topic': 'casual conversation',
                            'language': 'english'
                        }
                        message_content = await llm_client.generate_proactive_message(context)
                elif target_lang == 'italian':
                    if any(w in message_content.lower() for w in [' the ',' and ',' but ',' you ',' i ',' ok ']):
                        context = {
                            'context': 'general chat',
                            'server_name': channel.guild.name if hasattr(channel, 'guild') else '',
                            'suggested_topic': 'casual conversation',
                            'language': 'italian'
                        }
                        message_content = await llm_client.generate_proactive_message(context)
            
            try:
                message_content = await llm_client.rewrite_safe_text(message_content, target_lang if 'target_lang' in locals() else 'english')
            except Exception as mod_err:
                log_to_file("MODERATE", f"Rewrite failed: {mod_err}")
            
            is_safe, reason = self.safety_filter.is_safe(message_content)
            if not is_safe:
                log_to_file("SAFETY_BLOCK", f"Blocked send_message: {reason}")
                return

            typing_time = len(message_content) / random.uniform(5.0, 9.0)
            if typing_time > 0.5:
                async with channel.typing():
                    await asyncio.sleep(typing_time)
            
            await channel.send(message_content)
            log_to_file("RESPONSE", f"Sent message in {channel.name}: {message_content}")
            
            await db_manager.save_bot_response(
                discord_message_id=f'sent_{datetime.now().timestamp()}',
                channel_id=channel_id,
                content=message_content,
                action_type='SEND',
                server_id=channel.guild.id if hasattr(channel, 'guild') else None
            )
            
            await db_manager.save_log('SEND_MESSAGE', f'Message sent in {channel.name}')
        
        except Exception as e:
            print(f"Message sending error: {e}")
    
    async def cleanup_last_bot_message(self, channel_id: int):
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                return
            async for msg in channel.history(limit=20):
                if msg.author.id == self.user.id:
                    try:
                        await msg.delete()
                        log_to_file("CLEANUP", f"Deleted message {msg.id} in {channel.name}")
                        break
                    except Exception as e:
                        log_to_file("CLEANUP", f"Delete failed: {e}")
                        break
        except Exception as e:
            log_to_file("CLEANUP", f"Cleanup failure: {e}")
    
    async def send_dm(self, action_plan: Dict):
        try:
            user_id = action_plan.get('target_user')
            if not user_id:
                return
            
            user = self.get_user(int(user_id))
            if not user:
                return
            
            message_content = action_plan.get('message')
            if not message_content:
                context = {
                    'context': 'direct message',
                    'server_name': 'DM',
                    'suggested_topic': 'casual conversation'
                }
                message_content = await llm_client.generate_proactive_message(context)
            
            is_safe, reason = self.safety_filter.is_safe(message_content)
            if not is_safe:
                log_to_file("SAFETY_BLOCK", f"Blocked DM: {reason}")
                return

            typing_time = len(message_content) / random.uniform(5.0, 9.0)
            if typing_time > 0.5:
                 async with user.typing():
                    await asyncio.sleep(typing_time)

            await user.send(message_content)
            
            await db_manager.save_bot_response(
                discord_message_id=f'dm_{datetime.now().timestamp()}',
                channel_id='DM',
                content=message_content,
                action_type='DM_SEND',
                is_dm=True
            )
            
            await db_manager.save_log('SEND_DM', f'DM sent to {user.name}')
        
        except Exception as e:
            print(f"DM sending error: {e}")
    
    async def read_messages(self, action_plan: Dict):
        try:
            channel_id = action_plan.get('target_channel')
            if not channel_id:
                return
            
            channel = self.get_channel(int(channel_id))
            if not channel:
                return
            
            async for message in channel.history(limit=20):
                if message.author == self.user:
                    continue
                
                msg_data = {
                    'id': message.id,
                    'author': message.author.id,
                    'author_name': message.author.name,
                    'content': message.content,
                    'channel': message.channel.id,
                    'channel_name': message.channel.name,
                    'guild': message.guild.id if message.guild else None,
                    'guild_name': message.guild.name if message.guild else None,
                    'is_dm': isinstance(message.channel, discord.DMChannel),
                    'timestamp': datetime.now().isoformat()
                }
                
                if msg_data not in self.recent_messages:
                    self.recent_messages.append(msg_data)
            
            await db_manager.save_log('READ_MESSAGES', f'Read messages from {channel.name}')
        
        except Exception as e:
            print(f"Message reading error: {e}")
    
    async def get_stats(self):
        user_stats = await db_manager.get_user_stats()
        message_stats = await db_manager.get_message_stats()
        
        return {
            'total_users': user_stats[0],
            'suspicious_users': user_stats[1],
            'total_suspicions': user_stats[2],
            'total_messages': message_stats[0],
            'dm_messages': message_stats[1],
            'bot_responses': message_stats[2],
            'servers': len(self.guilds),
            'active_channels': len(self.active_channels)
        }
    
    async def close(self):
        await db_manager.close()
        await super().close()

def main():
    token = os.getenv('DISCORD_BOT_TOKEN')
    print(f"Token caricato: {token}")
    
    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables")
        log_to_file("FATAL", "DISCORD_BOT_TOKEN missing")
        return
    
    bot = DiscordAIBot()
    
    try:
        log_to_file("STARTUP", "Attempting to login with token...")
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        print(f"Error: Invalid Discord Bot Token ({token}). Please check your .env file.")
        log_to_file("FATAL", f"Login failed: Invalid Token {token}")
    except discord.errors.ConnectionClosed as e:
        try:
            code = getattr(e, 'code', None)
        except Exception:
            code = None
        if code == 4004:
            print(f"Error: WebSocket closed (4004). Invalid token or auth failure. Token: {token}") 
            log_to_file("FATAL", "WS closed 4004: Invalid Token/Auth")
        else:
            print(f"Connection closed: {e}")
            log_to_file("FATAL", f"Connection closed: {e}")
    except Exception as e:
        print(f"Fatal error during bot execution: {e}")
        log_to_file("FATAL", f"Fatal error: {e}")

if __name__ == '__main__':
    main()
