import asyncio
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from src.config import Config
from src.engines.base import BaseAIEngine


class CliRunnerEngine(BaseAIEngine):
    """
    Asynchronous CLI runner engine for Claude Code, Gemini CLI, OpenCode,
    and customizable CLI commands. Fully compatible with Windows, macOS, and Linux.
    """

    def __init__(self, config: Config):
        self.config = config

    def _build_env(self) -> Dict[str, str]:
        """Prepares environment variables including API keys and UTF-8 enforcement."""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        if self.config.gemini_api_key:
            env["GEMINI_API_KEY"] = self.config.gemini_api_key
        if self.config.anthropic_api_key:
            env["ANTHROPIC_API_KEY"] = self.config.anthropic_api_key
        if self.config.openai_api_key:
            env["OPENAI_API_KEY"] = self.config.openai_api_key
        if self.config.openai_base_url:
            env["OPENAI_BASE_URL"] = self.config.openai_base_url
        if self.config.openai_model_name:
            env["OPENAI_MODEL"] = self.config.openai_model_name

        return env

    def _resolve_command(self, prompt: str, project_path: Path, read_only: bool) -> str:
        """Constructs the command line string based on AI_ENGINE configuration."""
        engine = self.config.ai_engine

        if engine == "claude":
            # Claude Code CLI
            # In read-only mode, we add a prompt instruction not to edit files
            prefix = "READ-ONLY REQUEST (Do not edit or create files): " if read_only else ""
            escaped_prompt = f"{prefix}{prompt}".replace('"', '\\"')
            return f'claude -p "{escaped_prompt}"'

        elif engine == "gemini":
            # Official Gemini CLI
            prefix = "READ-ONLY: " if read_only else ""
            escaped_prompt = f"{prefix}{prompt}".replace('"', '\\"')
            return f'gemini --prompt "{escaped_prompt}"'

        elif engine == "opencode":
            # OpenCode / Aider style CLI
            prefix = "/ask " if read_only else ""
            escaped_prompt = f"{prefix}{prompt}".replace('"', '\\"')
            return f'opencode run "{escaped_prompt}"'

        elif engine == "custom":
            if not self.config.custom_cli_cmd:
                raise ValueError("AI_ENGINE is set to 'custom' but CUSTOM_CLI_CMD is empty in .env!")
            prefix = "READ-ONLY: " if read_only else ""
            formatted = self.config.custom_cli_cmd.format(
                prompt=f"{prefix}{prompt}",
                project_path=str(project_path),
            )
            return formatted

        else:
            raise ValueError(f"Unsupported CLI engine type: '{engine}'")

    async def _execute_command(self, cmd_str: str, project_path: Path) -> str:
        """
        Runs the command in project_path with timeout and process-tree termination.
        """
        env = self._build_env()
        is_windows = platform.system() == "Windows"

        try:
            # Use create_subprocess_shell for seamless shell & .cmd/.bat alias resolution on Windows
            proc = await asyncio.create_subprocess_shell(
                cmd_str,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.config.command_timeout,
                )
            except asyncio.TimeoutError:
                # Terminate the process tree on timeout
                if is_windows:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        capture_output=True,
                    )
                else:
                    proc.kill()
                return f"⏳ Execution timed out after {self.config.command_timeout} seconds."

            out_text = stdout.decode("utf-8", errors="replace").strip()
            err_text = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                error_msg = err_text if err_text else out_text
                return f"❌ Command failed (Exit code {proc.returncode}):\n{error_msg}"

            return out_text if out_text else "Command completed successfully with no output."

        except Exception as e:
            return f"❌ Subprocess execution error: {str(e)}"

    async def ask(self, prompt: str, project_path: Path) -> str:
        cmd_str = self._resolve_command(prompt, project_path, read_only=True)
        return await self._execute_command(cmd_str, project_path)

    async def ask_general(self, prompt: str) -> str:
        # For CLI runners, run from base directory
        base_dir = Path.cwd()
        cmd_str = self._resolve_command(prompt, base_dir, read_only=True)
        return await self._execute_command(cmd_str, base_dir)

    async def execute(self, prompt: str, project_path: Path) -> str:
        cmd_str = self._resolve_command(prompt, project_path, read_only=False)
        return await self._execute_command(cmd_str, project_path)
