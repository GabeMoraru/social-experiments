"""A stand-in chat model, so the experiments' loops run offline: no key, no cost, nothing sent."""

from types import SimpleNamespace

import pytest

from social_experiments import agents


class Scripted:
    """Answers every call with one tool call whose arguments come from policy(messages)."""

    def __init__(self, tool, policy):
        self.tool, self.policy = tool, policy

    def bind_tools(self, tools, **_):
        return self

    def invoke(self, messages):
        return SimpleNamespace(
            tool_calls=[{'name': self.tool, 'args': self.policy(messages), 'id': f'call-{len(messages)}'}],
            content=[{'type': 'thinking', 'thinking': 'scripted'}],
            response_metadata={'stop_reason': 'tool_use'},
            usage_metadata={'input_tokens': 10, 'output_tokens': 5},
        )


@pytest.fixture
def offline(tmp_path, monkeypatch):
    """Run in an empty folder with a scripted model: recordings and ledger lines land there, and nothing is sent.
    Call it with the tool's name and a policy giving that tool's arguments."""
    monkeypatch.chdir(tmp_path)

    def use(tool, policy):
        monkeypatch.setattr(agents, 'chat', lambda: Scripted(tool, policy))

    return use
