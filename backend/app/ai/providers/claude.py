"""The paid-Vendor stub. Disabled by default and gated on a Board decision.

Gate 3 in the plan forbids paid APIs for the demo. This class exists so the
provider registry has the same shape for all three providers; it never makes a
network call unless both ``AI_ENABLE_CLAUDE=1`` and a board approval flag are
set explicitly. Even then, it is a stub that raises ``ProviderUnavailable``.
"""
from __future__ import annotations

import os

from ..types import ExtractionResult, FieldDef, ProviderUnavailable


class ClaudeProvider:
    name = "claude"
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")
    paid = True

    def enabled(self) -> bool:
        return (os.environ.get("AI_ENABLE_CLAUDE") == "1"
                and os.environ.get("BOARD_APPROVED_PAID_API") == "1")

    def available(self) -> tuple[bool, str]:
        if not self.enabled():
            return False, "disabled: paid API, gated on a Board decision (Gate 3)"
        return False, "stub: no paid provider is implemented for the demo"

    def extract(self, document_text: str, document_type: str,
                fields: list[FieldDef], *, prompt_version: str | None = None) -> ExtractionResult:
        raise ProviderUnavailable(self.available()[1])
