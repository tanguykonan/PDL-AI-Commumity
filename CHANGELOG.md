# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-25

### Initial Open-Source Community Edition Release

#### 🚀 Added
- **Core AI & Chat Engine**:
  - LLM integration with **Groq API** (`llama-3.3-70b-versatile`) featuring ultra-low inference latency.
  - Dynamic AI Function Calling tools: real-time web search, server diagnostics, weather lookup, time reporting, and knowledge base vector retrieval.
  - Dual-tier DDR memory system:
    - `DDR1`: Fast volatile short-term conversational context memory.
    - `DDR2`: Persistent long-term user profile, interaction history, and contextual tracking.
- **RAG (Retrieval-Augmented Generation) Architecture**:
  - `TSE (Tutorial Search Engine)`: Semantic vector search powered by **ChromaDB** with automated document chunking for `.md`, `.txt`, `.docx`, and `.pdf` files.
  - `ISE (Internal Search Engine)`: Server-level contextual log indexing in JSONL format.
  - `WSE (Web Search Engine)`: Real-time web intelligence querying powered by the **Tavily Search API**.
- **Discord Slash & Prefix Commands**:
  - `/help`: User commands (`ping`, `infos`, `commands`, `support`).
  - `/staff`: Moderation commands with hierarchy checks (`config` UI panel, `punish`, `contest`, `clear`).
  - `/music`: Full-featured audio playback suite powered by **Lavalink v4** (`play`, `stop`, `pause`, `resume`, `skip`, `queue`, `nowplaying`, `volume`).
  - `+root`: Developer & maintainer administration commands (`stats`, `status`, `blacklist`, `broadcast`, `channel`, `quit`).
- **Vision & Media Processing**:
  - Asynchronous OCR image text extraction pipeline powered by **Tesseract OCR** and **Pillow**.
- **System Monitoring**:
  - Real-time hardware health check metrics: CPU, RAM, Disk I/O, GPU (via GPUtil), and Network bandwidth tracking.
- **Customization & Templates**:
  - Modular persona prompts configuration via `settings/resources/strings/prompts.toml`.
  - Knowledge base guide template in `settings/resources/strings/tutoriels.md`.
- **Infrastructure & Deployment**:
  - `Dockerfile` with multi-stage Python 3.11 build and Tesseract OCR integration.
  - `docker-compose.yml` for unified bot, Lavalink v4, and persistent storage orchestration.

#### 🔧 Changed
- Decoupled all private enterprise dependencies, webhooks, and private API configurations into modular open-source configuration templates.
- Fully standardized all codebase comments, docstrings (`"""..."""`), and module headers into clean technical English following **PEP 8** and **PEP 257**.
- Converted database transactions into thread-safe, atomic disk operations with fallback schemas.

#### 🔒 Security
- Strict `.env` encapsulation for API tokens and server secrets.
- Hierarchy validation ensuring server owners and bot roles cannot be moderated accidentally.
- Blacklist controls for abusive servers and bad actors.
