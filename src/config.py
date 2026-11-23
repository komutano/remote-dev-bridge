import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set
from dotenv import load_dotenv

# Base directory for the repository
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


@dataclass
class ProjectInfo:
    alias: str
    path: Path
    description: str = ""


class Config:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not self.telegram_token:
            raise ValueError(
                "CRITICAL: TELEGRAM_BOT_TOKEN is missing! "
                "Please configure it in your .env file."
            )

        # Parse and validate allowed Telegram user IDs (Fail-fast security requirement)
        raw_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
        if not raw_allowed:
            raise ValueError(
                "CRITICAL SECURITY LOCK: ALLOWED_USER_IDS is empty! "
                "For zero-trust security, the bot will not start without at least one authorized Telegram user ID."
            )

        self.allowed_user_ids: Set[int] = set()
        for uid_str in raw_allowed.split(","):
            cleaned = uid_str.strip()
            if cleaned:
                if not cleaned.isdigit():
                    raise ValueError(f"Invalid Telegram User ID in ALLOWED_USER_IDS: '{cleaned}' (must be numeric)")
                self.allowed_user_ids.add(int(cleaned))

        if not self.allowed_user_ids:
            raise ValueError("CRITICAL SECURITY LOCK: No valid numeric IDs found in ALLOWED_USER_IDS.")

        # Engine settings
        self.ai_engine = os.getenv("AI_ENGINE", "gemini-direct").strip().lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()
        self.openai_model_name = os.getenv("OPENAI_MODEL_NAME", "meta/llama-3.3-70b-instruct").strip()
        self.custom_cli_cmd = os.getenv("CUSTOM_CLI_CMD", "").strip()

        # IDE launcher and timeout
        self.ide_command = os.getenv("IDE_COMMAND", "code").strip()
        try:
            self.command_timeout = int(os.getenv("COMMAND_TIMEOUT", "300"))
        except ValueError:
            self.command_timeout = 300

        # Git commit identity
        self.git_author_name = os.getenv("GIT_COMMIT_AUTHOR_NAME", "RemoteDevBridge").strip()
        self.git_author_email = os.getenv("GIT_COMMIT_AUTHOR_EMAIL", "bot@remotedevbridge.local").strip()

        # Load projects mapping
        self.projects: Dict[str, ProjectInfo] = self._load_projects()

    def _load_projects(self) -> Dict[str, ProjectInfo]:
        projects_file = BASE_DIR / "projects.json"
        if not projects_file.exists():
            print(
                "[WARNING] 'projects.json' not found. "
                "Creating a default template from projects.example.json or please create one.",
                file=sys.stderr,
            )
            return {}

        try:
            with open(projects_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse 'projects.json': {e}")

        projects_dict: Dict[str, ProjectInfo] = {}
        for alias, item in data.items():
            if not isinstance(item, dict) or "path" not in item:
                continue
            path_obj = Path(item["path"]).resolve()
            description = item.get("description", "")
            projects_dict[alias.lower().strip()] = ProjectInfo(
                alias=alias.lower().strip(),
                path=path_obj,
                description=description,
            )

        return projects_dict

    def get_project(self, alias: str) -> Optional[ProjectInfo]:
        """Lookup project by alias (case-insensitive)."""
        return self.projects.get(alias.lower().strip())

    def is_user_authorized(self, user_id: int) -> bool:
        """Check if Telegram user id is in the allowed list."""
        return user_id in self.allowed_user_ids


# Global cached config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
