import asyncio
import functools
import io
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable

from telegram import Update
from telegram.constants import ChatAction
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from src.config import Config, get_config
from src.engines import create_engine
from src.engines.base import BaseAIEngine
from src import git_guard
from src.utils import path_guard, text_helpers


def auth_required(func: Callable):
    """
    Decorator that enforces strict user ID authorization.
    Silently ignores requests from unauthorized Telegram IDs.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        config: Config = context.bot_data["config"]

        if not config.is_user_authorized(user_id):
            # Strict Zero-Trust: Silent drop to prevent discovery
            print(f"[SECURITY] Unauthorized access attempt blocked from Telegram ID: {user_id}")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


async def _keep_typing(context: ContextTypes.DEFAULT_TYPE, chat_id: int, stop_event: asyncio.Event):
    """Continuously renews the typing action every 4 seconds until task finishes."""
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=4.0)
        except asyncio.TimeoutError:
            continue


async def _reply_safe(update: Update, text: str, as_code: bool = False, lang: str = ""):
    """
    Sends long text responses split across multiple Telegram messages.
    Falls back gracefully to plain text if Markdown parsing fails.
    """
    if as_code:
        # Wrap content in code block chunks
        chunks = text_helpers.split_message(text, max_length=3800)
        for chunk in chunks:
            formatted = text_helpers.format_code_block(chunk, language=lang)
            try:
                await update.effective_message.reply_text(formatted, parse_mode="Markdown")
            except BadRequest:
                # Fallback to plain text on Markdown parse error
                await update.effective_message.reply_text(chunk)
    else:
        chunks = text_helpers.split_message(text, max_length=3900)
        for chunk in chunks:
            try:
                await update.effective_message.reply_text(chunk)
            except Exception as e:
                print(f"[ERROR] Failed to send message: {e}")


# =====================================================================
# COMMAND HANDLERS
# =====================================================================

@auth_required
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows system status and command reference."""
    config: Config = context.bot_data["config"]
    msg = (
        "🌉 *RemoteDevBridge Online*\n\n"
        f"🤖 *Active Engine:* `{config.ai_engine}`\n"
        f"🖥️ *IDE Command:* `{config.ide_command}`\n"
        f"📁 *Configured Projects:* {len(config.projects)}\n\n"
        "*Available Commands:*\n"
        "• `/projects` - List all configured projects\n"
        "• `/status <proj>` - Check git branch & clean status\n"
        "• `/diff <proj>` - View unstaged/staged code changes\n"
        "• `/push <proj> [msg]` - Stage, commit & push current branch\n"
        "• `/ask <proj> <question>` - Read-only code analysis\n"
        "• `/do <proj> <instruction>` - Auto-branch & execute code edit\n"
        "• `/ls <proj> [subfolder]` - Browse project files securely\n"
        "• `/file <proj> <filepath>` - Read or download file content\n"
        "• `/open <proj> [filepath]` - Launch on desktop editor\n"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")


@auth_required
async def cmd_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists all configured projects from projects.json."""
    config: Config = context.bot_data["config"]
    if not config.projects:
        await update.effective_message.reply_text(
            "⚠️ No projects found in `projects.json`.\n"
            "Please configure your project aliases and paths."
        )
        return

    lines = ["📁 *Configured Projects:*\n"]
    for alias, proj in config.projects.items():
        exists_mark = "✅" if proj.path.exists() else "❌ (Path not found)"
        desc = f" - _{proj.description}_" if proj.description else ""
        lines.append(f"• `{alias}`: {exists_mark}{desc}\n  Path: `{proj.path}`")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth_required
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows git status of the project."""
    if not context.args:
        await update.effective_message.reply_text("Usage: `/status <project_alias>`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    config: Config = context.bot_data["config"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project alias: `{alias}`. Use `/projects`.", parse_mode="Markdown")
        return

    status_text = await git_guard.get_status_short(proj.path)
    branch = await git_guard.get_current_branch(proj.path)
    header = f"📊 *Git Status:* `{alias}` (Branch: `{branch}`)\n"
    await _reply_safe(update, f"{header}\n{status_text}", as_code=True)


@auth_required
async def cmd_diff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows git diff of changes in the project."""
    if not context.args:
        await update.effective_message.reply_text("Usage: `/diff <project_alias>`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    config: Config = context.bot_data["config"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    diff_text = await git_guard.get_diff(proj.path)
    await _reply_safe(update, diff_text, as_code=True, lang="diff")


@auth_required
async def cmd_push(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stages all changes, creates a commit and pushes current branch to origin."""
    if not context.args:
        await update.effective_message.reply_text("Usage: `/push <project_alias> [commit message]`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    commit_msg = " ".join(context.args[1:]).strip() if len(context.args) > 1 else None

    config: Config = context.bot_data["config"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    lock = git_guard.lock_manager.get_lock(alias)
    if lock.locked():
        info = git_guard.lock_manager.get_active_info(alias)
        started_str = info[0].strftime("%H:%M:%S") if info else "earlier"
        await update.effective_message.reply_text(
            f"⚠️ Project `{alias}` is currently busy with another operation (Started: {started_str}). Please wait.",
            parse_mode="Markdown"
        )
        return

    async with lock:
        git_guard.lock_manager.mark_started(alias, "/push")
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(context, update.effective_chat.id, stop_typing))
        try:
            success, msg = await git_guard.stage_commit_and_push(
                proj.path,
                commit_message=commit_msg,
                author_name=config.git_author_name,
                author_email=config.git_author_email,
            )
            prefix = "🚀 *Git Push Success!*\n\n" if success else "❌ *Git Push Failed!*\n\n"
            await update.effective_message.reply_text(f"{prefix}{msg}", parse_mode="Markdown")
        finally:
            stop_typing.set()
            await typing_task
            git_guard.lock_manager.mark_finished(alias)


@auth_required
async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executes read-only code analysis."""
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: `/ask <project_alias> <question>`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    question = " ".join(context.args[1:]).strip()

    config: Config = context.bot_data["config"]
    engine: BaseAIEngine = context.bot_data["engine"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    lock = git_guard.lock_manager.get_lock(alias)
    if lock.locked():
        info = git_guard.lock_manager.get_active_info(alias)
        started_str = info[0].strftime("%H:%M:%S") if info else "earlier"
        await update.effective_message.reply_text(
            f"⚠️ Project `{alias}` is busy (Started: {started_str}). Please wait.",
            parse_mode="Markdown"
        )
        return

    async with lock:
        git_guard.lock_manager.mark_started(alias, "/ask")
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(context, update.effective_chat.id, stop_typing))
        try:
            await update.effective_message.reply_text(f"🔍 Analyzing `{alias}` in read-only mode...")
            response = await engine.ask(question, proj.path)
            await _reply_safe(update, response)
        finally:
            stop_typing.set()
            await typing_task
            git_guard.lock_manager.mark_finished(alias)


@auth_required
async def cmd_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Safely executes code modifications:
    1. Checks for uncommitted working tree changes.
    2. Auto-creates mobile/YYYYMMDD-HHMMSS branch.
    3. Runs AI instruction.
    4. Reports modified files summary and diff.
    """
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: `/do <project_alias> <instruction>`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    instruction = " ".join(context.args[1:]).strip()

    config: Config = context.bot_data["config"]
    engine: BaseAIEngine = context.bot_data["engine"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    # 1. Concurrency Lock check
    lock = git_guard.lock_manager.get_lock(alias)
    if lock.locked():
        info = git_guard.lock_manager.get_active_info(alias)
        started_str = info[0].strftime("%H:%M:%S") if info else "earlier"
        await update.effective_message.reply_text(
            f"⚠️ Project `{alias}` is busy (Started: {started_str}). Please wait.",
            parse_mode="Markdown"
        )
        return

    async with lock:
        git_guard.lock_manager.mark_started(alias, "/do")
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(context, update.effective_chat.id, stop_typing))

        try:
            # 2. Dirty working tree protection
            is_clean, dirty_info = await git_guard.check_clean_working_tree(proj.path)
            if not is_clean:
                await update.effective_message.reply_text(
                    f"⚠️ *Working tree is dirty in `{alias}`!*\n\n"
                    "Uncommitted local changes exist on your PC. To protect your work, execution was aborted.\n"
                    "Use `/status` or `/diff` to inspect.",
                    parse_mode="Markdown"
                )
                return

            # 3. Create isolated mobile branch
            branch_ok, branch_result = await git_guard.create_mobile_branch(proj.path)
            if not branch_ok:
                await update.effective_message.reply_text(f"❌ Git safety error:\n{branch_result}")
                return

            await update.effective_message.reply_text(
                f"🌿 Created branch `{branch_result}`.\n"
                f"⏳ Executing instruction with `{config.ai_engine}`...",
                parse_mode="Markdown"
            )

            # 4. Run AI instruction
            output = await engine.execute(instruction, proj.path)
            await _reply_safe(update, output)

            # 5. Diff summary
            diff_summary = await git_guard.get_diff(proj.path, stat_only=True)
            summary_msg = (
                f"\n\n📊 *Changes Summary on `{branch_result}`:*\n"
                f"```text\n{diff_summary}\n```\n\n"
                f"💡 Next steps: Use `/diff {alias}` to view full code differences or `/push {alias} [message]` to push to GitHub!"
            )
            await _reply_safe(update, summary_msg)

        finally:
            stop_typing.set()
            await typing_task
            git_guard.lock_manager.mark_finished(alias)


@auth_required
async def cmd_ls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Safely lists files and folders inside project directory."""
    if not context.args:
        await update.effective_message.reply_text("Usage: `/ls <project_alias> [relative_folder]`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    sub_path = context.args[1] if len(context.args) > 1 else ""

    config: Config = context.bot_data["config"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    try:
        dirs, files, is_truncated = path_guard.list_directory_entries(proj.path, sub_path)
    except path_guard.SecurityPathError as e:
        await update.effective_message.reply_text(f"🛡️ Security Block: {str(e)}")
        return

    lines = [f"📂 *Directory:* `{alias}` / `{sub_path or '.'}`\n"]
    if dirs:
        lines.append("*Directories:*")
        for d in dirs:
            lines.append(f" 📁 `{d}`")
    if files:
        lines.append("\n*Files:*")
        for f in files:
            lines.append(f" 📄 `{f}`")

    if not dirs and not files:
        lines.append("_(Directory is empty)_")

    if is_truncated:
        lines.append("\n⚠️ _[Output truncated: too many items]_")

    await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth_required
async def cmd_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Safely reads or downloads a file from the project directory."""
    if len(context.args) < 2:
        await update.effective_message.reply_text("Usage: `/file <project_alias> <relative_filepath>`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    file_rel_path = context.args[1]

    config: Config = context.bot_data["config"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    try:
        target_file = path_guard.resolve_safe_path(proj.path, file_rel_path)
    except path_guard.SecurityPathError as e:
        await update.effective_message.reply_text(f"🛡️ Security Block: {str(e)}")
        return

    if not target_file.is_file():
        await update.effective_message.reply_text(f"❌ Path is not a file or does not exist: `{file_rel_path}`", parse_mode="Markdown")
        return

    file_size = target_file.stat().st_size
    # If file is larger than 50KB or cannot be decoded as utf-8 text, send as file attachment
    if file_size > path_guard.MAX_INLINE_FILE_SIZE:
        await update.effective_message.reply_text(f"📦 Sending large file ({file_size // 1024} KB) as document...")
        with open(target_file, "rb") as f:
            await update.effective_message.reply_document(document=f, filename=target_file.name)
        return

    try:
        content = target_file.read_text(encoding="utf-8")
        ext = target_file.suffix.lstrip(".")
        await _reply_safe(update, content, as_code=True, lang=ext)
    except UnicodeDecodeError:
        # Binary file fallback
        with open(target_file, "rb") as f:
            await update.effective_message.reply_document(document=f, filename=target_file.name)


@auth_required
async def cmd_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Launches the project or file in the desktop editor (e.g. VS Code, Antigravity)."""
    if not context.args:
        await update.effective_message.reply_text("Usage: `/open <project_alias> [relative_filepath]`", parse_mode="Markdown")
        return

    alias = context.args[0].lower()
    rel_path = context.args[1] if len(context.args) > 1 else ""

    config: Config = context.bot_data["config"]
    proj = config.get_project(alias)
    if not proj:
        await update.effective_message.reply_text(f"❌ Unknown project: `{alias}`", parse_mode="Markdown")
        return

    try:
        target_path = path_guard.resolve_safe_path(proj.path, rel_path)
    except path_guard.SecurityPathError as e:
        await update.effective_message.reply_text(f"🛡️ Security Block: {str(e)}")
        return

    ide_cmd = config.ide_command
    try:
        # Non-blocking desktop launch
        subprocess.Popen([ide_cmd, str(target_path)], shell=(os.name == "nt"))
        await update.effective_message.reply_text(
            f"🖥️ *Desktop IDE Launched!*\n\n"
            f"Command: `{ide_cmd}`\n"
            f"Target: `{target_path}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed to launch IDE `{ide_cmd}`:\n{str(e)}")


def setup_application(config: Config) -> Application:
    """Configures and returns the python-telegram-bot Application."""
    app = ApplicationBuilder().token(config.telegram_token).build()

    # Create AI engine instance
    engine = create_engine(config)

    # Attach shared state
    app.bot_data["config"] = config
    app.bot_data["engine"] = engine

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("projects", cmd_projects))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("diff", cmd_diff))
    app.add_handler(CommandHandler("push", cmd_push))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("do", cmd_do))
    app.add_handler(CommandHandler("ls", cmd_ls))
    app.add_handler(CommandHandler("file", cmd_file))
    app.add_handler(CommandHandler("open", cmd_open))

    return app
