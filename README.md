# 🧠 Cognitive Discord Interaction Framework  
### Bot Token Edition · Research & Controlled Testing

A cognitive, LLM-powered conversational simulation framework for Discord.  
Designed to model autonomous interaction patterns through action planning, safety constraints, and persistent local memory.

This repository publishes the **Bot Token Edition**, intended as a **reference implementation** for research and controlled testing.

---

## ⚠️ Legal Notice

> **Important**
>
> - Automating Discord user accounts violates the  
>   [Discord Terms of Service](https://discord.com/terms) and  
>   [Community Guidelines](https://discord.com/guidelines).
> - This project is released **strictly for educational and controlled testing purposes**.
> - Use at your own risk. The author assumes **no responsibility** for bans, suspensions, or other consequences.

---

## 📦 Editions

| Edition | Availability | Description |
|------|------|------|
| **Bot Token Edition** | Public (GitHub) | Reference implementation using a standard Discord Bot token |
| **Extended Discord Integration** | Commercial | Advanced adapters and extended capabilities under a research license |

> Extended Discord adapters and advanced integration layers are **intentionally excluded** from this public release.

For access to extended integrations, a **commercial research license** is required.

---

## ✨ Core Features

- **LLM-powered conversation engine**  
  Multi-provider support (GLM, OpenAI, Gemini)
- **Autonomous action planning**  
  Read · Reply · Send · DM orchestration
- **Suspicion-aware interaction handling**  
  Contextual response rewriting for realism
- **Safety & anti-abuse layer**  
  Regex-based filtering (invites, PII, scams, slurs)
- **Human-like behavior simulation**  
  Typing delay · Reading delay · Presence rotation · Sleep cycle
- **Local persistence**  
  Async SQLite logging via SQLAlchemy
- **Automatic language detection**  
  English / Italian via LLM inference

---

## 🏗️ Architecture Overview

**Core Components**
- Message intake & focus management
- Cognitive planner (action selection)
- Safety & policy filtering
- Persistent storage layer

**LLM Layer**
- Configurable providers (GLM / OpenAI / Gemini)
- Unified abstraction layer

**Persistence**
- Async SQLAlchemy
- SQLite local database

**Authentication**
- Standard Discord **Bot Token**
- No user-account automation included

---

## 🔧 Requirements

- Python **3.10+**
- Discord **Bot Token**
- LLM provider credentials (GLM / OpenAI / Gemini)

---

## 📥 Installation

### 1. Clone the repository
```bash
git clone https://github.com/HighMark-31/Cognitive-User-Simulation.git
cd Cognitive-User-Simulation
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Discord Bot Token
DISCORD_BOT_TOKEN=your_bot_token

# Database
DATABASE_URL=sqlite+aiosqlite:///discord_bot.db

# LLM provider: glm | openai | gemini
LLM_PROVIDER=glm

# GLM (Zhipu)
GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://api.z.ai/api/coding/paas/v4/
GLM_MODEL=glm-4.7

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.2

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3-flash-preview

# Optional: prioritize a specific server
PRIORITY_GUILD_ID=server_id
```

> `.env` variables are loaded with override to avoid conflicts with system environments.

---

## ▶️ Quick Start

```bash
python discord_bot.py
```

In controlled testing environments, the framework connects to the servers the bot belongs to and performs **simulated interactions** according to the configured cognitive rules.

---

## ⚙️ How It Works

### Action Planning

The system autonomously selects actions such as:

* **READ** – Collect contextual messages
* **REPLY** – Respond in-channel
* **SEND** – Initiate new messages
* **DM_SEND** – Send direct messages

### Suspicion Handling

* Detects suspicion related to automated or non-human behavior
* Logs events for analysis
* Rewrites replies to preserve interaction realism

### Safety & Anti-Abuse

* Blocks unsafe content before dispatch
* Simulates realistic delays and presence changes
* Implements circadian sleep cycles

---

## 🗄️ Data Persistence

Stored locally in SQLite:

* Users
* Messages
* Bot responses
* Structured interaction logs

---

## 🛠️ Configuration

* `mood` — default: `chill`
* `personality` — default:
  *sarcastic, direct, ironic, sometimes chaotic*
* `PRIORITY_GUILD_ID` — server prioritization
* LLM setup — configurable via `.env` and `LLM_Client.py`

---

## 🔐 Commercial Research License & Advanced Adapters

Advanced Discord adapters and extended integration layers are distributed **separately** under a **commercial research license**.

Licensed users receive:

* Adapter modules
* Integration guidelines
* Extended configuration options

---

## 📜 License

Released under a **Custom Research & Educational License**.
See the `LICENSE` file for full terms.

---

## 🆘 Support

* Open a GitHub issue for bugs or questions
* For extended integrations, request access under the commercial research license

