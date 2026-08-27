from __future__ import annotations

from worker.models.agent import AgentConfig, CodingAgent
from worker.models.registry import ModelRegistry


class FakeRuntime:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate(self, *args, **kwargs):
        return next(self.responses)


def test_agent_can_call_injected_tool_and_finish():
    seen = []

    def read_file(path):
        seen.append(path)
        return "hello"

    runtime = FakeRuntime([
        '{"action":"inspect","tool":"read_file","arguments":{"path":"README.md"},"reasoning":"inspect","done":false}',
        '{"action":"finish","tool":null,"arguments":{},"reasoning":"complete","done":true}',
    ])
    agent = CodingAgent(runtime, ModelRegistry.default(), {"read_file": read_file}, AgentConfig(max_steps=3))
    result = agent.run("inspect README")
    assert result["status"] == "COMPLETED"
    assert seen == ["README.md"]


def test_agent_rejects_empty_task():
    agent = CodingAgent(FakeRuntime([]))
    try:
        agent.run("")
    except ValueError as exc:
        assert "task" in str(exc)
    else:
        raise AssertionError("empty task must fail")
