# Contributing to PDL-AI

First off, thank you for considering contributing to **PDL-AI**! 🎉 

We welcome contributions from developers of all skill levels. Whether you are fixing a bug, adding new AI capabilities, improving documentation, or creating tutorials, your help makes this project better for everyone.

---

## 📜 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment Setup](#development-environment-setup)
4. [Project Structure Overview](#project-structure-overview)
5. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Adding New Slash Commands](#adding-new-slash-commands)
   - [Adding AI Tools](#adding-ai-tools)
   - [Adding AI Personas](#adding-ai-personas)
6. [Coding Guidelines & Standards](#coding-guidelines--standards)
7. [Commit Message Conventions](#commit-message-conventions)
8. [Pull Request Process](#pull-request-process)

---

## 🤝 Code of Conduct

By participating in this project, you agree to uphold a welcoming, respectful, and inclusive environment for everyone. Please be considerate, constructive, and open to feedback during discussions and code reviews.

---

## 🚀 Development Environment Setup

### Prerequisites

- **Python 3.11+** installed
- **Git** installed
- **Tesseract OCR** (optional, for image text extraction)
- **Java 17+** (optional, for local Lavalink audio node)

### Step-by-Step Setup

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/tanguykonan/PDL-AI-Community.git
   cd PDL-AI-Community
   ```

2. **Create and Activate a Virtual Environment**:
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your Discord Bot Token and Groq API Key:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GROQ_TOKEN=your_groq_api_key_here
   TAVILY_TOKEN=your_tavily_api_key_here  # Optional: for web search
   ```

5. **Run the Bot in Development Mode**:
   ```bash
   python run.py
   ```

---

## 📂 Project Structure Overview

```text
├── app/
│   ├── cluster/
│   │   ├── ram/ddr/       # Short-term (DDR1) and persistent (DDR2) memory
│   │   └── rom/           # Local databases and server interaction logs
│   ├── core/              # LLM orchestration (Groq API, tools, NeuroChat)
│   └── helps/             # Interactive UI builders and logging utilities
├── bot/                   # Discord client initialization and lifecycle events
├── commands/
│   ├── admin/             # Developer debug and moderation cogs
│   ├── custom/            # Maintenance prefix commands (+root)
│   └── public/            # Public slash commands (/help, /music, /staff)
├── plugins/
│   ├── integrating/       # Database management, Lavalink client, System monitor
│   └── processing/        # RAG modules (TSE, ISE, WSE) and OCR processing
├── settings/
│   ├── config/            # Central configuration parameter definitions
│   └── resources/strings/ # Prompts (prompts.toml) and RAG guides (tutoriels.md)
└── run.py                 # Application entrypoint
```

---

## 💡 How to Contribute

### Adding New Slash Commands

All slash commands are organized as Discord `commands.Cog` or `commands.GroupCog` classes inside the `commands/` directory:

1. Create or edit a cog in `commands/public/` or `commands/admin/`.
2. Ensure the command uses `@app_commands.command(...)` with clear descriptions.
3. Handle exceptions with `logger.error(..., exc_info=True)`.
4. Register the cog in the `setup(bot)` function at the bottom of the file.

### Adding AI Tools

To provide the AI with a new callable capability (e.g., querying an API or performing a calculation):

1. Define the tool function inside [`app/core/ai_tools.py`](file:///d:/Professionnel/My-Projects/PDL-AI-Community/app/core/ai_tools.py).
2. Add its JSON Schema definition to the `AI_TOOLS` list.
3. Map the execution in `execute_tool()` inside `ai_tools.py`.

### Adding AI Personas

Add new personality templates to [`settings/resources/strings/prompts.toml`](file:///d:/Professionnel/My-Projects/PDL-AI-Community/settings/resources/strings/prompts.toml):

```toml
[custom_persona]
name = "My Custom Assistant"
description = "A specialized helper persona."
prompt = """
You are a helpful coding assistant. You answer queries clearly with code examples.
"""
```

---

## 📐 Coding Guidelines & Standards

- **Language**: All codebase comments, docstrings (`"""..."""`), and variable names MUST be written in **clear, idiomatic English**.
- **Code Style**: Adhere to [PEP 8](https://peps.python.org/pep-0008/) and [PEP 257](https://peps.python.org/pep-0257/) standards.
- **Type Hinting**: Use type annotations wherever practical (e.g., `def handle_event(ctx: commands.Context) -> None:`).
- **Asynchronous Code**: Prefer `async`/`await` for all I/O, networking, and Discord interactions.
- **Error Handling**: Never use bare `except: pass`. Always catch specific exceptions and log them with `logger.error(...)`.
- **Validation**: Verify that all Python files compile cleanly before submitting:
  ```bash
  python -m compileall .
  ```

---

## 🏷️ Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` A new feature or capability (e.g., `feat(music): add autoplay option`)
- `fix:` A bug fix (e.g., `fix(ddr2): prevent null reference on missing user profile`)
- `docs:` Documentation changes only (e.g., `docs: update README quickstart`)
- `refactor:` Code changes that neither fix a bug nor add a feature
- `perf:` Performance improvements
- `test:` Adding or updating tests
- `chore:` Maintenance tasks, dependency updates, or docker configurations

---

## 🔄 Pull Request Process

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Make and Test Your Changes**:
   Ensure the bot starts up with `python run.py` and that `python -m compileall .` passes without errors.
3. **Commit Your Changes**:
   ```bash
   git commit -m "feat(module): descriptive summary of changes"
   ```
4. **Push to Your Fork**:
   ```bash
   git push origin feat/your-feature-name
   ```
5. **Open a Pull Request**:
   - Provide a clear title and description explaining what was changed and why.
   - Link any related issues or feature discussions.
   - Wait for review from the maintainers.

---

Thank you for helping make **PDL-AI** an incredible open-source community bot! 🚀
