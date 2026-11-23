from src.config import Config
from src.engines.base import BaseAIEngine
from src.engines.cli_runner import CliRunnerEngine
from src.engines.direct_gemini import DirectGeminiEngine
from src.engines.direct_nvidia import DirectNvidiaEngine


def create_engine(config: Config) -> BaseAIEngine:
    """Factory that instantiates the configured AI engine."""
    engine_name = config.ai_engine.lower().strip()

    if engine_name == "gemini-direct":
        return DirectGeminiEngine(config)
    elif engine_name == "nvidia":
        return DirectNvidiaEngine(config)
    elif engine_name in ("gemini", "claude", "opencode", "custom"):
        return CliRunnerEngine(config)
    else:
        raise ValueError(
            f"Unknown AI_ENGINE '{config.ai_engine}'. "
            "Supported values: 'gemini-direct', 'nvidia', 'gemini', 'claude', 'opencode', 'custom'."
        )
