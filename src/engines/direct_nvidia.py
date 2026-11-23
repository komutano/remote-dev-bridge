import asyncio
import json
import os
import urllib.request
from pathlib import Path
from typing import Optional
from src.config import Config
from src.engines.base import BaseAIEngine
from src.utils.path_guard import IGNORED_DIRECTORIES


class DirectNvidiaEngine(BaseAIEngine):
    """
    Direct NVIDIA NIM API Engine (build.nvidia.com).
    Connects to NVIDIA high-performance models (Nemotron, Llama 3, Mistral)
    via standard OpenAI-compatible API without requiring external CLI tools.
    """

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.openai_api_key
        self.base_url = config.openai_base_url.rstrip("/") if config.openai_base_url else "https://integrate.api.nvidia.com/v1"
        self.model_name = config.openai_model_name if config.openai_model_name and "llama-3.3" not in config.openai_model_name else "nvidia/nemotron-3.5-lightning-30b-a3b"

        if not self.api_key:
            raise ValueError(
                "NVIDIA API Key is missing! "
                "Please configure OPENAI_API_KEY with your 'nvapi-...' key in .env."
            )

    def _collect_project_summary(self, project_path: Path, max_files: int = 40) -> str:
        """Gathers a concise overview of project directory files for LLM context."""
        tree_lines = []
        count = 0
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]
            rel_root = os.path.relpath(root, project_path)
            prefix = "" if rel_root == "." else f"{rel_root}/"

            for file in sorted(files):
                count += 1
                if count > max_files:
                    tree_lines.append("... [additional files omitted for brevity]")
                    return "\n".join(tree_lines)
                tree_lines.append(f"- {prefix}{file}")

        return "\n".join(tree_lines) if tree_lines else "(Empty directory)"

    async def _call_nvidia_api(self, system_instruction: str, user_content: str) -> str:
        """Calls NVIDIA NIM chat completions API asynchronously."""
        def _sync_request():
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.2,
                "max_tokens": 2048,
            }

            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()

        try:
            return await asyncio.to_thread(_sync_request)
        except Exception as e:
            return f"❌ NVIDIA API Error: {str(e)}"

    async def ask(self, prompt: str, project_path: Path) -> str:
        """Read-only question and code analysis."""
        summary = self._collect_project_summary(project_path)
        system_instruction = (
            "You are an expert AI software engineer analyzing a local codebase remotely via Telegram using NVIDIA NIM. "
            "You are in READ-ONLY mode. Provide concise, clear, and actionable technical explanations in Turkish."
        )
        user_content = (
            f"Project File Structure:\n{summary}\n\n"
            f"User Question:\n{prompt}"
        )
        return await self._call_nvidia_api(system_instruction, user_content)

    async def ask_general(self, prompt: str) -> str:
        """General AI advisory mode (AML/CFT, coding, architecture)."""
        system_instruction = (
            "You are an expert AI consultant powered by NVIDIA NIM. "
            "Answer clearly, thoroughly, and concisely in Turkish with clean Markdown. "
            "Cover compliance (AML/CFT, blockchain intelligence), software engineering, and security."
        )
        return await self._call_nvidia_api(system_instruction, prompt)

    async def execute(self, prompt: str, project_path: Path) -> str:
        """Instruction execution mode."""
        summary = self._collect_project_summary(project_path)
        system_instruction = (
            "You are an expert AI software engineer working on a local codebase remotely via Telegram using NVIDIA NIM. "
            "Explain the exact changes, code snippets, or solutions required in Turkish."
        )
        user_content = (
            f"Project File Structure:\n{summary}\n\n"
            f"User Instruction:\n{prompt}"
        )
        return await self._call_nvidia_api(system_instruction, user_content)
