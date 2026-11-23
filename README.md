# RemoteDevBridge (remote-dev-bridge)

> **Bridge your mobile phone to your desktop AI coding agents and local repositories via Telegram.**  
> Code, analyze, diff, branch, push, and inspect projects from anywhere with Zero-Trust security and zero personal data leakage.

---

## 🌟 Vision: One Unified Bridge for All AI Layers

Developers often find themselves away from their desks when critical ideas strike or urgent bugs emerge. **RemoteDevBridge** transforms your smartphone into a secure remote control for your local developer workstation.

Instead of fragmenting your workflow across multiple isolated tools, **RemoteDevBridge unites every layer into a single, cohesive engine**:

```
                       📱 Your Smartphone (Telegram)
                                     │
                       🔐 Zero-Trust Auth & Git Guard
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
┌──────────────────────┐                           ┌──────────────────────┐
│  AI Engine Adapter   │                           │  Workspace & Git Ops │
├──────────────────────┤                           ├──────────────────────┤
│ 1. Google AI Studio  │ (Direct API, zero CLI)    │ • /status & /diff    │
│ 2. Claude Code CLI   │ (claude -p)               │ • /do (auto-branch)  │
│ 3. Gemini CLI        │ (Official CLI)            │ • /push (commit & PR)│
│ 4. OpenCode & NVIDIA │ (NVIDIA NIM, Ollama)      │ • /ls & /file viewer │
│ 5. Custom CLI / Aider│ (Configurable templates)  │ • /open (IDE launch) │
└──────────────────────┘                           └──────────────────────┘
```

You do **not** need VS Code or Antigravity open on your desktop to use this bridge. The AI runs headless in the background while your screen is locked. Whenever you want your desktop editor ready when you return to your desk, a single `/open` command brings up the project in your favorite IDE.

---

## 🚀 Key Highlights & Capabilities

### 1. Universal AI Engine Support
- **Direct Google AI Studio (`AI_ENGINE=gemini-direct`):** Zero setup required. Plug in your free Google AI Studio key and harness Gemini's 1M+ context window to inspect entire repositories without installing npm/pip CLI wrappers.
- **Official Gemini CLI (`AI_ENGINE=gemini`):** Seamless terminal execution of Google's CLI tools.
- **Claude Code CLI (`AI_ENGINE=claude`):** Run Anthropic's agentic CLI with automated non-interactive flags.
- **OpenCode & NVIDIA NIM (`AI_ENGINE=opencode`):** Connect to NVIDIA's high-performance AI inference (Llama 3.3 70B, DeepSeek R1/V3) or local Ollama models using the standard OpenAI-compatible protocol.
- **Custom Scripting (`AI_ENGINE=custom`):** Plug in Aider, aider-chat, or your proprietary shell scripts.

### 2. Complete End-to-End Git Workflow from Telegram
- **/do `<project> <instruction>`:** Automatically creates an isolated git branch (`mobile/YYYYMMDD-HHMMSS`), runs the instruction, and returns a summary of touched files.
- **/status `<project>`:** Instant `git status -sb` feedback.
- **/diff `<project>`:** View code modifications line-by-line right in chat or as patches.
- **/push `<project> [message]`:** Stages changes (`git add -A`), creates a commit, and pushes the mobile branch to `origin`. You can then review and open a Pull Request right from GitHub mobile.

### 3. File Explorer & Desktop Launcher
- **/ls `<project> [folder]`:** Securely browse folder structures with automatic filtering of `.git`, `node_modules`, and cache folders.
- **/file `<project> <path>`:** View text files inside chat or download large/binary files as Telegram document attachments.
- **/open `<project> [path]`:** Triggers your desktop editor (Antigravity, VS Code, Cursor) to launch the project on your monitor before you sit down.

---

## 🛡️ Zero-Trust Security & Anti-Leak Safeguards

This repository is designed from day one to be 100% public-ready with zero exposure of personal credentials:

1. **Strict User Whitelisting:** The bot validates the incoming Telegram User ID against `ALLOWED_USER_IDS`. Unauthorized users are silently rejected. If this variable is empty, the bot refuses to boot.
2. **Path Traversal Guard:** Every path requested via `/ls`, `/file`, or `/open` is verified using strict canonical resolution. Accessing files outside the project root is blocked.
3. **Dirty Working Tree Protection:** Before `/do` creates a branch or applies changes, it verifies `git status --porcelain`. If you left uncommitted local changes on your workstation, the operation aborts to prevent overwriting your in-progress work.
4. **Concurrency Lock (`ProjectLock`):** Per-project asynchronous locks prevent overlapping CLI processes or Git index locking conflicts.
5. **Windows 11 UTF-8 Encoding:** Forces `PYTHONIOENCODING=utf-8` and clean process tree termination (`taskkill`) on Windows.

---

## ⚡ Quick Start (2 Minutes)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/remote-dev-bridge.git
cd remote-dev-bridge

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 📱 Step-by-Step Telegram Bot & Identity Setup

To use this bridge securely, you need your own Telegram bot token and your permanent numeric Telegram User ID.

### A. Create Your Bot & Get Token (BotFather)
1. Open Telegram and search for **`@BotFather`** (the official verified bot).
2. Start the chat and send the command **`/newbot`**.
3. Choose a friendly **Display Name** (e.g. `Dev Bridge`).
4. Choose a unique **Username** ending in `bot` or `_bot` (e.g. `my_devbridge_bot`).
5. BotFather will provide your **HTTP API Token** (`7891234567:AAFl...`). Copy and paste this into `TELEGRAM_BOT_TOKEN` in `.env`.

### B. Discover Your Permanent Numeric Telegram User ID
In Telegram, changing your `@username` never alters your underlying **Numeric User ID**. RemoteDevBridge authenticates you via this permanent ID:
1. Search for **`@userinfobot`** or **`@raw_data_bot`** on Telegram and hit Start.
2. Note your numeric ID (e.g. `Id: 123456789`).
3. Set this in `.env` under `ALLOWED_USER_IDS` (`ALLOWED_USER_IDS=123456789`).

> [!IMPORTANT]
> **Zero-Trust Enforcement:** If `ALLOWED_USER_IDS` is omitted or empty, the bot refuses to launch. Unauthorized messages from strangers are silently dropped without response.

### C. Recommended Privacy Setting
To prevent anyone from adding your private bridge bot to random public groups:
- In `@BotFather`, run `/setjoingroups`, select your bot, and click **`Disable`**.

---

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your values:
```env
TELEGRAM_BOT_TOKEN=7891234567:AAFlKj9_xYzAbCdEfGhIjKlMnOpQrStUvWx
ALLOWED_USER_IDS=123456789

# Choose your engine:
AI_ENGINE=gemini-direct
GEMINI_API_KEY=AIzaSyYourGoogleAIStudioKeyHere

# Desktop editor launcher:
IDE_COMMAND=code
```

### 3. Configure Your Projects (`projects.json`)
Copy `projects.example.json` to `projects.json`:
```bash
cp projects.example.json projects.json
```
Define your local project mappings:
```json
{
  "my-app": {
    "path": "C:/Projects/my-app",
    "description": "Production Web App"
  },
  "api": {
    "path": "C:/Projects/backend-api",
    "description": "FastAPI Microservice"
  }
}
```

### 4. Run

#### Windows (One-Click Launcher):
Simply double-click **`start_bot.bat`** in the repository folder!

#### Command Line:
```bash
python main.py
```

> [!IMPORTANT]
> **Keeping the Process Running:**  
> RemoteDevBridge executes commands locally on your machine. Therefore, **the terminal window and your computer must remain running.**  
> - **Locking Your Screen is Fine:** You can lock your workstation (`Win + L`) when leaving your desk; the bot continues running headlessly in the background.  
> - **Minimize to Taskbar:** You can safely minimize the console window.  
> - **If Closed or Sleeping:** If you terminate the console window or the PC goes into sleep/shut-down mode, the bot goes offline. Messages sent while offline will be queued by Telegram and automatically processed as soon as you relaunch the bot.

---

## 📲 Mobile Quick-Action `[Menu]` Button

RemoteDevBridge automatically registers all available commands with Telegram's servers on startup (`set_my_commands`):
- **Menu Button:** A blue `[Menu]` button appears right next to the text input box in your Telegram mobile app.
- **Autocompletion:** Tap the menu button or type `/` in the chat to see a popup list of all commands and descriptions.
- **Cache Refresh:** If the button does not appear immediately, either type `/` once in the chat or restart your Telegram app to refresh its local cache.

---

## 📋 Telegram Commands Cheat Sheet

| Command | Description |
| :--- | :--- |
| `/start` | View system status, active engine, and help menu |
| `/engine [name]` | **AI Engine Switcher:** Switch between Google Gemini, NVIDIA NIM, and Claude via buttons or text |
| `/ai <question>` | **General AI Advisory:** Ask anything without a project (AML/CFT, architecture, coding) |
| `/projects` | List all configured project aliases and directory health |
| `/status <proj>` | Check branch name and working tree status |
| `/diff <proj>` | Inspect line-by-line differences of unstaged/staged edits |
| `/push <proj> [msg]` | Stage all changes, commit, and push branch to origin |
| `/ask [proj] <q>` | Analyze project codebase (falls back to general question if no project given) |
| `/do <proj> <inst>` | Auto-branch and apply code modifications with AI |
| `/ls <proj> [dir]` | Explore folders (traversal-safe, ignores build artifacts) |
| `/file <proj> <path>` | Read source files or download documents |
| `/open <proj> [path]` | Open target project/file in your desktop IDE |

---

## 🗺️ Roadmap & Future Horizons

RemoteDevBridge is evolving rapidly to deliver the ultimate mobile development and autonomous agent experience:

- [x] **v1.0 (Current Release):**
  - ✅ Dual native cloud engines: Google AI Studio (Gemini) & NVIDIA NIM (Nemotron).
  - ✅ On-the-fly interactive engine switcher (`/engine`) with Telegram inline buttons.
  - ✅ Zero-Trust authorization, path traversal protection, and Git working tree safeguards.
  - ✅ Full mobile Git lifecycle (`/do`, `/status`, `/diff`, `/push`).
  - ✅ File explorer (`/ls`, `/file`) and remote desktop IDE launcher (`/open`).
  - ✅ General AI advisory mode (`/ai` for AML/CFT, architecture, coding).

- [ ] **v1.5 (In Progress):**
  - 🔄 **Interactive Human-in-the-Loop PTY Bridge:** Stream interactive CLI prompts (Claude Code, Aider, OpenCode) directly to Telegram. When an agent pauses to ask for confirmation (*"Proceed with file edit? (Y/n)"*), interactive buttons (`[ ✅ Approve ]` / `[ ❌ Reject ]`) appear in chat, and responses are piped to the terminal in real-time.
  - 🔄 **Multi-Channel Adapters:** Discord bot and Slack webhook integrations.

- [ ] **v2.0 (Planned Milestones):**
  - 🚀 **Native Antigravity IDE Integration (MCP Server):** Dedicated MCP server and webhook bridge connecting Antigravity directly to Telegram. Receive real-time progress updates and approve pending agent actions while away from your desk.
  - 🎙️ **Voice-to-Code:** Transcribe Telegram voice notes directly into actionable code modifications via Gemini audio understanding.

---

## 🙏 Developer Acknowledgments & Special Thanks

As developers building on the frontier of agentic engineering, we would like to express our heartfelt gratitude to:

- **Google AI Studio Team:** For providing lightning-fast Gemini models, extraordinary context windows, and a generous developer free tier that makes autonomous remote coding accessible to every independent developer across the globe.
- **NVIDIA:** For pioneering the **NVIDIA NIM** developer platform, democratizing open weights models (Llama 3.3, DeepSeek, Mistral), and delivering world-class GPU inference infrastructure via standard developer-friendly APIs.

---

## 📄 License

Distributed under the permissive [MIT License](LICENSE). Built for the open-source developer community.
