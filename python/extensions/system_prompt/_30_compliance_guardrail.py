from typing import Any

from agent import Agent, LoopData
from python.helpers import guardrail
from python.helpers.extension import Extension


class ComplianceGuardrailPrompt(Extension):
    """Tells the agent that an out-of-band guardrail screens its tool calls."""

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any,
    ):
        policy = guardrail.get_policy()
        if policy.mode == guardrail.MODE_OFF:
            return
        system_prompt.append(
            self.agent.read_prompt(
                "agent.system.compliance.md",
                mode=policy.mode,
                approval_prefix=guardrail.APPROVAL_PREFIX,
            )
        )
