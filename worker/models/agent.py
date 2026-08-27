"""Guarded coding-agent loop. Tools are injected by the host runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .ollama_runtime import OllamaRuntime
from .registry import ModelRegistry

Tool = Callable[..., Any]


@dataclass(frozen=True)
class AgentConfig:
    model_name: str = "coding"
    max_steps: int = 20
    max_output_chars: int = 12000


class CodingAgent:
    def __init__(self, runtime: OllamaRuntime, registry: ModelRegistry | None = None,
                 tools: dict[str, Tool] | None = None, config: AgentConfig | None = None) -> None:
        self.runtime = runtime
        self.registry = registry or ModelRegistry.default()
        self.tools = dict(tools or {})
        self.config = config or AgentConfig()

    def _tool_manifest(self) -> str:
        return json.dumps({name: "available" for name in sorted(self.tools)}, ensure_ascii=False)

    def run(self, task: str, context: str = "") -> dict[str, Any]:
        if not task.strip():
            raise ValueError("task is required")
        spec = self.registry.get(self.config.model_name)
        prompt = (
            "You are a software-engineering agent working on a local repository.\n"
            "Plan before modifying anything. Never claim a tool was executed unless its result is supplied.\n"
            "Use concise JSON with keys: action, tool, arguments, reasoning, done.\n\n"
            f"Available tools: {self._tool_manifest()}\n"
            f"Repository context:\n{context[-30000:]}\n\nTask:\n{task}"
        )
        history: list[dict[str, Any]] = []
        for step in range(1, self.config.max_steps + 1):
            text = self.runtime.generate(spec.model, prompt, temperature=spec.temperature, context=spec.context_window)
            text = text[: self.config.max_output_chars]
            try:
                decision = json.loads(text)
            except json.JSONDecodeError:
                history.append({"step": step, "type": "model_output", "output": text})
                prompt += f"\nPrevious output was not valid JSON. Return valid JSON only:\n{text}"
                continue
            history.append({"step": step, "decision": decision})
            if decision.get("done") is True:
                return {"status": "COMPLETED", "steps": history, "final": decision}
            tool_name = decision.get("tool")
            if not tool_name:
                prompt += "\nNo tool selected. Select an available tool or set done=true."
                continue
            tool = self.tools.get(tool_name)
            if tool is None:
                prompt += f"\nTool {tool_name!r} is unavailable. Choose from: {sorted(self.tools)}"
                continue
            try:
                result = tool(**(decision.get("arguments") or {}))
                result_text = str(result)[-12000:]
            except Exception as exc:
                result_text = f"TOOL_ERROR: {type(exc).__name__}: {exc}"
            prompt += f"\nTool {tool_name} result:\n{result_text}\nContinue the task."
        return {"status": "MAX_STEPS", "steps": history}


__all__ = ["CodingAgent", "AgentConfig"]
