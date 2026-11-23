from src.config import Config
from src.engines.base import BaseAIEngine
from src.engines.cli_runner import CliRunnerEngine
from src.engines.direct_gemini import DirectGeminiEngine
from src.engines.direct_nvidia import DirectNvidiaEngine


def create_engine_by_name(engine_name: str, config: Config) -> BaseAIEngine:
    """Instantiates a specific AI engine by name."""
    name = engine_name.lower().strip()
    if name in ("gemini-direct", "gemini"):
        return DirectGeminiEngine(config)
    elif name in ("nvidia", "nvidia-nim"):
        return DirectNvidiaEngine(config)
    elif name in ("claude", "opencode", "custom"):
        return CliRunnerEngine(config)
    else:
        raise ValueError(
            f"Unknown AI engine: '{engine_name}'. "
            "Supported options: 'gemini-direct', 'nvidia', 'claude', 'opencode', 'custom'."
        )


def create_engine(config: Config) -> BaseAIEngine:
    """Factory that instantiates the configured AI engine."""
    return create_engine_by_name(config.ai_engine, config)
