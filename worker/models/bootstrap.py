"""Bootstrap helpers for the local PC AI stack.

This does not download model weights. The operator can install Ollama separately,
then run `ollama pull qwen2.5-coder:7b` on the PC.
"""

from __future__ import annotations

import os
from pathlib import Path

from .agent import CodingAgent
from .context import ProjectContext
from .ollama_runtime import OllamaRuntime
from .registry import ModelRegistry
from .repository_tools import RepositoryTools


def build_coding_agent(repo_root: str | Path) -> CodingAgent:
    root = Path(repo_root).resolve()
    tools = RepositoryTools(root)
    context = ProjectContext(root)
    runtime = OllamaRuntime(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        request_timeout=float(os.getenv("OLLAMA_REQUEST_TIMEOUT", "1800")),
    )
    registry = ModelRegistry.default()
    injected_tools = {
        "list_directory": tools.list_directory,
        "read_file": tools.read_file,
        "write_file": tools.write_file,
        "search_code": tools.search_code,
        "git_status": tools.git_status,
        "git_diff": tools.git_diff,
        "run_tests": tools.run_tests,
    }
    agent = CodingAgent(runtime=runtime, registry=registry, tools=injected_tools)
    agent.project_snapshot = context.snapshot()  # type: ignore[attr-defined]
    return agent


__all__ = ["build_coding_agent"]
