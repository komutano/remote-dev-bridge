import asyncio
import os
from pathlib import Path
from typing import Optional
from src.config import Config
from src.engines.base import BaseAIEngine
from src.utils.path_guard import IGNORED_DIRECTORIES


class DirectGeminiEngine(BaseAIEngine):
    """
    Direct Google AI Studio API Engine.
    Communicates directly with Google AI Studio using the modern Google GenAI SDK
    without requiring any external CLI tools (npm/pip) to be installed.
    """

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.gemini_api_key
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured! "
                "Get your free key from https://aistudio.google.com/ and add it to your .env file."
            )

    def _collect_project_summary(self, project_path: Path, max_files: int = 40) -> str:
        """Gathers a concise overview of project directory files for LLM context."""
        tree_lines = []
        count = 0
        for root, dirs, files in os.walk(project_path):
            # Prune ignored directories
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

    async def _call_gemini_api(self, system_instruction: str, user_content: str) -> str:
        """Calls Google AI Studio API asynchronously via google-genai SDK."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return (
                "❌ The 'google-genai' package is not installed.\n"
                "To use the direct Google AI Studio engine, please run:\n"
                "pip install google-genai"
            )

        def _sync_generate():
            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )

            # Preferred candidate models with automatic fallback
            candidates = [
                self.config.gemini_model,
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemini-3.8-flash",
                "gemma-4-26b-a4b-it",
            ]
            # Remove duplicates preserving order
            unique_models = []
            for m in candidates:
                if m and m not in unique_models:
                    unique_models.append(m)

            last_error = None
            for model_name in unique_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=user_content,
                        config=config,
                    )
                    if response.text:
                        return response.text
                except Exception as err:
                    last_error = err
                    continue

            return f"❌ Google AI Studio API Error (All models failed): {str(last_error)}"

        try:
            return await asyncio.to_thread(_sync_generate)
        except Exception as e:
            return f"❌ Google AI Studio API Error: {str(e)}"

    async def ask(self, prompt: str, project_path: Path) -> str:
        """Read-only question and code analysis."""
        summary = self._collect_project_summary(project_path)
        system_instruction = (
            "You are an expert AI software engineer analyzing a local codebase remotely via Telegram. "
            "You are currently in READ-ONLY mode. Provide concise, clear, and actionable technical explanations. "
            "Do not instruct file changes directly since write mode is disabled for this query."
        )
        user_content = (
            f"Project File Structure:\n{summary}\n\n"
            f"User Question/Request:\n{prompt}"
        )
        return await self._call_gemini_api(system_instruction, user_content)

    async def ask_general(self, prompt: str) -> str:
        """General AI advisory mode: answers any technical, compliance, or architecture question directly."""
        system_instruction = (
            "You are an expert AI consultant and senior engineer communicating remotely via Telegram. "
            "Answer the user's question clearly, thoroughly, and concisely with structured markdown. "
            "Cover software engineering, algorithms, security, and architecture with high technical accuracy."
        )
        return await self._call_gemini_api(system_instruction, prompt)

    async def execute(self, prompt: str, project_path: Path) -> str:
        """Instruction execution mode."""
        summary = self._collect_project_summary(project_path)
        system_instruction = (
            "You are an expert AI software engineer working on a local codebase remotely via Telegram. "
            "The user has opened a dedicated git branch for modifications. "
            "Explain the exact changes, code snippets, or architectural solutions required for their instruction. "
            "Provide full modified files or diff blocks when appropriate."
        )
        user_content = (
            f"Project File Structure:\n{summary}\n\n"
            f"User Task Instruction:\n{prompt}"
        )
        return await self._call_gemini_api(system_instruction, user_content)
