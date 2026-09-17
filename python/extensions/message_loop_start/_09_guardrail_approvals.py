from typing import Any

from agent import LoopData
from python.helpers import guardrail
from python.helpers.extension import Extension
from python.helpers.print_style import PrintStyle


class GuardrailApprovals(Extension):
    """Registers USER GATE approvals typed by the human.

    The guardrail blocks a tool call that would send personal data or
    credentials off this machine and prints a single-use token. Only the human
    can produce that token, so the agent cannot approve its own egress.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs: Any):
        seen: set[str] = set()
        for message in (loop_data.user_message, self.agent.last_user_message):
            if message is None:
                continue
            try:
                text = message.output_text()
            except Exception:
                continue
            for approval_id in guardrail.extract_approval_ids(text):
                if approval_id in seen:
                    continue
                seen.add(approval_id)
                if guardrail.grant_approval(approval_id):
                    note = f"Guardrail: user approval {approval_id} registered (single use)"
                    PrintStyle(font_color="orange", padding=True).print(note)
                    self.agent.context.log.log(type="warning", content=note)
