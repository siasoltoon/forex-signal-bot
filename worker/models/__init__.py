"""Local model and coding-agent runtime for the PC worker."""

from .registry import ModelSpec, ModelRegistry
from .ollama_runtime import OllamaRuntime
from .agent import CodingAgent, AgentConfig

__all__ = ["ModelSpec", "ModelRegistry", "OllamaRuntime", "CodingAgent", "AgentConfig"]
