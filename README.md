# PDL-AI — Community Edition

PDL-AI Community is an advanced, modular Discord AI bot built with Python, discord.py, and Groq LLMs. It features multi-layered conversational memory, local vector-based RAG, real-time web search capabilities, interactive configuration panels, Lavalink audio streaming, and moderation tools.

---

## Key Features

- **Conversational Intelligence**: Ultra-fast LLM inference powered by Groq API with integrated function calling and autonomous agent tools.
- **DDR Memory Architecture**: Multi-layer memory engine handling short-term conversation context (`deque`) and persistent user/server profiles stored locally in JSON.
- **Dual RAG Engine**:
  - **ISE (Internal Search Engine)**: Direct local indexing and context retrieval of server activity logs.
  - **TSE (Tutorial Search Engine)**: 100% local semantic document search powered by ChromaDB vector embeddings.
- **Agentic Web Search (WSE)**: Real-time search engine integration via Tavily API.
- **Audio Streaming**: Lavalink integration supporting voice channels, queues, volume control, and YouTube cipher integration.
- **Interactive UI Panel**: Discord Select Menus and interactive Views for server-level configuration (languages, modes, authorized channels, auto-sanctions).
- **System Monitoring**: Real-time host hardware diagnostics (CPU cores/freq/temps, RAM/Swap, Disks, GPU, and Uptime).
- **Administration & Moderation**: Complete command suite for moderation (`/modo`), staff administration (`/staff`), diagnostics (`/debug`), and maintenance (`+root`).

---

## Customization: Prompts & Knowledge Base

PDL-AI Community is designed to be easily customized by server administrators and developers:

### 1. Customizing AI Personas (`prompts.toml`)
The AI personalities and system instructions are stored in [`settings/resources/strings/prompts.toml`](settings/resources/strings/prompts.toml).

You can customize existing modes or define new ones:
- `default`: The main personality used across standard conversations.
- `caveman`: Primitive, humorous roleplay.
- `eric_cartman`: Sarcastic, sharp-witted roleplay.
- `homer_simpson`: Casual and comedic persona.
- `support`: Strict, factual technical assistant.

Server administrators can switch between available personas at runtime directly from Discord using `/staff config`.

### 2. Customizing Server Knowledge Base & RAG (`tutoriels.md`)
The Tutorial Search Engine (TSE) indexes [`settings/resources/strings/tutoriels.md`](settings/resources/strings/tutoriels.md) into a local vector database (**ChromaDB**).

- Write your own server rules, FAQs, installation guides, and documentation using standard Markdown headings (`# Title`, `## Section`).
- The bot automatically chunks, embeds, and indexes this file locally on startup.
- When users ask questions about your server, games, rules, or guides, the AI semantically searches this document and provides accurate answers.
- Supporting document formats: `.md`, `.txt`, `.docx`, `.pdf`.

---

## Prerequisites

- **Python**: 3.11 or higher
- **Discord Bot Token**: From the [Discord Developer Portal](https://discord.com/developers/applications)
- **Groq API Key**: From [Groq Console](https://console.groq.com)
- **Tavily API Key** *(optional, for web search)*: From [Tavily AI](https://tavily.com)
- **Java 17+** *(if running Lavalink locally)* or **Docker**

---

## Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/tanguykonan/PDL-AI-Community.git
cd PDL-AI-Community
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
NAME=pdl
PREFIX=+
VERSION="2.1.2"
DISCORD_TOKEN=your_discord_bot_token_here

SUPPORT_CHANNEL=your_support_channel_id_here
SUPPORT_MEMBERS="(your_admin_user_id_1, your_admin_user_id_2)"

GROQ_TOKEN=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

TAVILY_TOKEN=your_tavily_api_key_here

LAVALINK_HOST=localhost
LAVALINK_PORT=2333
LAVALINK_PASS=your_lavalink_password_here
```

### 5. Run the bot
```bash
python run.py
```

---

## Docker Deployment

To deploy the bot alongside Lavalink and YouTube Cipher using Docker Compose:

```bash
# 1. Configure your environment
cp .env.example .env

# 2. Start all services in the background
docker compose up -d --build

# 3. View bot logs
docker compose logs -f pdl-ai
```

---

## Project Structure

```
PDL-AI-Community/
├── app/
│   ├── cluster/
│   │   ├── ram/ddr/          # DDR memory engine (DDR1 & DDR2)
│   │   └── rom/              # Local persistence (databases, logs, users)
│   ├── core/
│   │   ├── ai_tools.py       # Function calling & tool implementations
│   │   ├── main.py           # Bot event loops & background tasks
│   │   └── neurochat.py      # LLM chat engine & context builder
│   └── helps/
│       ├── config_ui.py      # Interactive Discord Views & Select components
│       └── utils.py          # Helpers & logging configuration
├── bot/
│   ├── bot.py                # Main bot instance initialization
│   └── client.py             # Discord client configuration
├── commands/
│   ├── admin/                # Debug & Moderation command groups
│   ├── custom/               # Prefix commands (+root)
│   └── public/               # Public commands (Help, Music, Staff)
├── lavalink/
│   └── application.yml       # Lavalink server configuration
├── plugins/
│   ├── integrating/
│   │   ├── hosting/          # System monitor (node_vm) & Lavalink node client
│   │   └── storing/          # Local JSON database engine
│   └── processing/
│       ├── agenticRag/       # ISE (server logs), TSE (vector DB), WSE (web search)
│       └── analyzer/         # OCR & Security analyzers
├── settings/
│   ├── config/params.py      # Central configuration loader
│   └── resources/            # Prompts and tutorial documents
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── run.py
```

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
