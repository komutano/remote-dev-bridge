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

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your values:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
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
```bash
python main.py
```
Open Telegram, message your bot `/start`, and enjoy mobile development freedom!

---

## 📋 Telegram Commands Cheat Sheet

| Command | Description |
| :--- | :--- |
| `/start` | View system status, active engine, and help menu |
| `/projects` | List all configured project aliases and directory health |
| `/status <proj>` | Check branch name and working tree status |
| `/diff <proj>` | Inspect line-by-line differences of unstaged/staged edits |
| `/push <proj> [msg]` | Stage all changes, commit, and push branch to origin |
| `/ask <proj> <q>` | Ask questions in read-only mode (does not alter files) |
| `/do <proj> <inst>` | Auto-branch and apply code modifications with AI |
| `/ls <proj> [dir]` | Explore folders (traversal-safe, ignores build artifacts) |
| `/file <proj> <path>` | Read source files or download documents |
| `/open <proj> [path]` | Open target project/file in your desktop IDE |

---

## 🙏 Developer Acknowledgments & Special Thanks

As developers building on the frontier of agentic engineering, we would like to express our heartfelt gratitude to:

- **Google AI Studio Team:** For providing lightning-fast Gemini models, extraordinary context windows, and a generous developer free tier that makes autonomous remote coding accessible to every independent developer across the globe.
- **NVIDIA:** For pioneering the **NVIDIA NIM** developer platform, democratizing open weights models (Llama 3.3, DeepSeek, Mistral), and delivering world-class GPU inference infrastructure via standard developer-friendly APIs.

---

## 📄 License

Distributed under the permissive [MIT License](LICENSE). Built for the open-source developer community.
