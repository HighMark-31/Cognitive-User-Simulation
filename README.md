<div align="center">

# 🧠 Cognitive User Simulation

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Custom-red.svg)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Bot-5865F2.svg)](https://discord.com)
[![LLM](https://img.shields.io/badge/LLM-Multi--Provider-brightgreen.svg)](#)

**An advanced LLM-powered conversational simulation framework for Discord**

*Featuring autonomous action planning, safety filtering, and multi-provider LLM integration for research and controlled testing*

[Features](#-features) • [Installation](#-installation) • [Configuration](#%EF%B8%8F-configuration) • [Usage](#-usage) • [Documentation](#-documentation)

</div>

---

## ⚠️ LEGAL WARNING: EXPERIMENTAL SOFTWARE

> [!CRITICAL]
> 
> ### DISCORD TERMS OF SERVICE VIOLATION RISK
> 
> This project is a **SOCIAL EXPERIMENT** and **EDUCATIONAL TOOL** designed to study AI interaction patterns.
> 
> **WARNING:** The use of "Self-Bots" (automating user accounts) is a **DIRECT VIOLATION** of [Discord Terms of Service](https://discord.com/terms) and [Community Guidelines](https://discord.com/guidelines).
> 
> ### BY USING THIS SOFTWARE, YOU ACKNOWLEDGE THAT:
> 
> 1. ✅ You are using this strictly in **private, controlled test environments**
> 2. ❌ You will **NOT** use this on your main personal account (Risk of Permanent Ban)
> 3. ❌ You will **NOT** use this to spam, harass, or disrupt public servers
> 4. ⚖️ The author assumes **NO RESPONSIBILITY** for account bans, suspensions, or legal consequences
> 
> **🔴 USE AT YOUR OWN RISK 🔴**

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🤖 AI & Intelligence
- 🧠 **Advanced LLM Integration** (GLM 4.7, OpenAI, Gemini)
- 🎯 **Autonomous Action Planning System**
- 🌐 **Multilingual Support** with automatic detection
- 🔍 **Suspicion Detection & Logging**
- 💬 **Natural Conversational Responses**

</td>
<td width="50%">

### 🛡️ Safety & Security
- 🔒 **Advanced Safety Filter** (regex-based)
- 🚫 **Anti-ToS Violation Protection**
- 👤 **Human Behavior Simulation**
- 💤 **Circadian Rhythm Sleep Mode**
- ✅ **Message Acknowledgment System**

</td>
</tr>
<tr>
<td width="50%">

### 📊 Data & Analytics
- 💾 **SQLite Database** for all interactions
- 📈 **Usage Statistics Tracking**
- 🔎 **Interaction Logging**
- 📝 **Suspicion Event Recording**

</td>
<td width="50%">

### 🎭 Behavior Simulation
- ⌨️ **Typing Indicators** (length-based timing)
- 👀 **Reading Delays** (context-aware)
- 🎨 **Presence Management** (Online/Idle/DND)
- 🎮 **Activity Rotation** (VS Code, Spotify, etc.)

</td>
</tr>
</table>

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- A Discord user token (⚠️ testing environments only)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/HighMark-31/Cognitive-User-Simulation.git
cd Cognitive-User-Simulation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Run the bot
python discord_bot.py
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# ==========================================
# DISCORD CONFIGURATION
# ==========================================
DISCORD_USER_TOKEN=your_discord_user_token_here

# ==========================================
# DATABASE CONFIGURATION
# ==========================================
DATABASE_URL=sqlite+aiosqlite:///discord_bot.db

# ==========================================
# LLM PROVIDER SELECTION
# ==========================================
# Options: glm | openai | gemini
LLM_PROVIDER=glm

# ==========================================
# GLM (Zhipu AI) CONFIGURATION
# ==========================================
GLM_API_KEY=your_glm_api_key_here
GLM_BASE_URL=https://open.bigmodel.cn/api/coding/paas/v4
GLM_MODEL=glm-4.7

# ==========================================
# OPENAI CONFIGURATION
# ==========================================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# ==========================================
# GOOGLE GEMINI CONFIGURATION
# ==========================================
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# ==========================================
# OPTIONAL SETTINGS
# ==========================================
PRIORITY_GUILD_ID=1320998163615846420
```

---

## 🔑 Getting Credentials

### 🚫 Discord User Token

> [!CAUTION]
> **IMPORTANT: TERMS OF SERVICE (ToS) VIOLATION**
> 
> Using a user token (self-botting) is a **direct violation of Discord's Terms of Service**. This practice can lead to **permanent account suspension**.
> 
> **RECOMMENDATIONS:**
> - ❌ **DO NOT** use this script with your main account
> - ✅ Use the user token **exclusively in secure and controlled test environments**
> - 📚 This project is intended only for educational purposes and social research
> - ⚖️ The author assumes no responsibility for misuse or sanctions

<details>
<summary><b>Click to view how to obtain a Discord User Token</b></summary>

1. Open Discord in your browser (not the desktop app)
2. Press `F12` to open Developer Tools
3. Go to the **Network** tab
4. Send a message in any channel
5. Find a request (like `messages`) in the Network tab
6. Look for the `Authorization` header in the request headers
7. Copy the value and add it to your `.env` file as `DISCORD_USER_TOKEN`

</details>

### 🤖 LLM Provider API Keys

| Provider | Get API Key | Documentation |
|----------|-------------|---------------|
| **GLM (Zhipu)** | [open.bigmodel.cn](https://open.bigmodel.cn/) | [Docs](https://open.bigmodel.cn/dev/howuse/introduction) |
| **OpenAI** | [platform.openai.com](https://platform.openai.com/) | [Docs](https://platform.openai.com/docs) |
| **Google Gemini** | [makersuite.google.com](https://makersuite.google.com/) | [Docs](https://ai.google.dev/docs) |

---

## 🚀 Usage

### Starting the Bot

```bash
python discord_bot.py
```

The bot will automatically:
- 🔗 Connect to all servers it's present in
- 💬 Monitor messages in channels and DMs
- 🤖 Generate contextual responses using the configured LLM
- 💾 Log all interactions to the database

### Viewing Statistics

```bash
python stats_viewer.py
```

---

## 📚 Documentation

### Action Planning System

The bot autonomously decides what to do next using LLM-based planning:

| Action | Description |
|--------|-------------|
| `READ` | Read messages from channels to understand context |
| `REPLY` | Reply to messages in channels |
| `SEND` | Send new messages to channels |
| `DM_REPLY` | Reply to direct messages |
| `DM_SEND` | Send new direct messages |

### Suspicion Handling

When a user questions if the bot is an AI:

1. 🔍 Automatically detects suspicion patterns
2. 💾 Logs the interaction to database
3. 🎭 Generates a natural denial response
4. 📊 Saves data for analysis

### Multi-Provider LLM Support

Switch between providers by changing `LLM_PROVIDER` in `.env`:

```env
LLM_PROVIDER=glm     # Zhipu GLM-4.7
LLM_PROVIDER=openai  # GPT-4o-mini
LLM_PROVIDER=gemini  # Gemini 1.5 Flash
```

### Safety & Anti-Ban Features

#### 🔒 Safety Filter
Hard-coded regex patterns block:
- 🔗 Discord invites
- 👤 PII (Personal Identifiable Information)
- 💰 Scam keywords
- 🚫 Slurs and toxic content

#### 👤 Human Simulation
- ⌨️ **Typing Indicators**: Simulates realistic typing time based on message length
- 👀 **Reading Delays**: Adds natural reading time before responding
- 🎨 **Presence Management**: Rotates status (Online, Idle, DND) and activities
- 💤 **Sleep Mode**: Implements circadian rhythm with nighttime inactivity

#### ✅ Message Acknowledgment
Marks messages as read to clear notification indicators, simulating real UI interaction.

---

## 🗄️ Database Structure

### Tables

```
┌─────────────────────────────────────┐
│ users                               │
├─────────────────────────────────────┤
│ Information about interacted users  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ messages                            │
├─────────────────────────────────────┤
│ All received messages               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ bot_responses                       │
├─────────────────────────────────────┤
│ All bot responses                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ interactions                        │
├─────────────────────────────────────┤
│ Interaction logs                    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ social_test_logs                    │
├─────────────────────────────────────┤
│ General social test logs            │
└─────────────────────────────────────┘
```

All data is saved in `discord_bot.db` (SQLite).

---

## 🎨 Advanced Configuration

### Personality Customization

Modify the bot's personality in `discord_bot.py`:

```python
mood = 'chill'  # Options: chill, energetic, serious, playful
personality = 'sarcastic, direct, ironic, sometimes chaotic'
```

### Response Generation Rules

- 📝 2-3 natural, colloquial sentences
- 🎯 Reference concrete details from context
- 🗣️ Moderate use of slang/abbreviations
- 😊 Minimal emojis
- 🌐 Adapt to channel language (EN/IT)

**Examples:**

| User Message | Bot Response |
|--------------|--------------|
| "Can someone help me?" | "Tell me, what do you need a hand with?" |
| "This code doesn't work" | "Let's talk—what part doesn't add up?" |

---

## 🔧 Troubleshooting

<details>
<summary><b>Bot doesn't respond</b></summary>

- ✅ Verify the token in `.env`
- ✅ Check Discord Developer Portal privileges
- ✅ Review logs for errors
- ✅ Ensure bot has permission to read/send messages

</details>

<details>
<summary><b>LLM API Error</b></summary>

- ✅ Verify the API key is valid
- ✅ Check available credits on your LLM account
- ✅ Verify the base URL is correct
- ✅ Test API connection manually

</details>

<details>
<summary><b>Bot doesn't save data</b></summary>

- ✅ Verify write permissions in the directory
- ✅ Check `.env` configuration
- ✅ Ensure SQLite is properly installed
- ✅ Review `database.py` for errors

</details>

<details>
<summary><b>Switching LLM Providers</b></summary>

1. Update `LLM_PROVIDER` in `.env`
2. Ensure the corresponding API key is set
3. Restart the bot
4. The bot will automatically initialize with the new provider

</details>

---

## 📁 Project Structure

```
Cognitive-User-Simulation/
│
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
│
├── discord_bot.py            # Main bot entry point
├── LLM_Client.py             # LLM provider integration
├── database.py               # Database models and operations
├── safety_filter.py          # Safety and content filtering
├── stats_viewer.py           # Statistics viewer utility
│
├── requirements.txt          # Python dependencies
├── LICENSE                   # Project license
└── README.md                 # This file
```

---

## 📜 License

This project is for **educational and testing purposes only**. Use it responsibly.

See [LICENSE](LICENSE) file for more details.

---

## 🙏 Support

For issues or questions:
- 📝 Check the logs in the database or `debug.txt`
- 🐛 Open an issue in the repository
- 📧 Contact the author through GitHub

---

## 🔗 Links

- [Discord Terms of Service](https://discord.com/terms)
- [Discord Community Guidelines](https://discord.com/guidelines)
- [Discord Developer Portal](https://discord.com/developers)

---

<div align="center">

**Made with ❤️ for educational and research purposes**

⭐ **Star this repo if you found it interesting!** ⭐

</div>
