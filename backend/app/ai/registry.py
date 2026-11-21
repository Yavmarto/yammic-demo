"""Versioned prompt registry.

Prompt files live next to this module in ``prompts/extract_v*.md``. A run records
``<version>@<sha256-prefix>`` so the exact prompt text can be reproduced and
audited. ``GET /ai/prompts`` exposes the same registry.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
PATTERN = re.compile(r"^extract_(v\d+)\.md$")


@dataclass(frozen=True)
class Prompt:
    version: str
    text: str
    sha256: str
    path: Path

    @property
    def tag(self) -> str:
        """Version plus a short hash, safe for the ``prompt_version`` DB column."""
        return f"{self.version}@{self.sha256[:12]}"

    def render(self, fields: list[dict], document_type: str) -> str:
        lines = []
        for f in fields:
            bits = [f"- `{f['id']}` ({f.get('label', f['id'])}, {f.get('valueType') or 'string'})"]
            if f.get("unit"):
                bits.append(f"unit: {f['unit']}")
            if f.get("terminology"):
                bits.append(f"target code: {f['terminology'].get('system')} {f['terminology'].get('code')}")
            if f.get("help"):
                bits.append(f"note: {f['help']}")
            lines.append("; ".join(bits))
        return (self.text
                .replace("{{FIELDS}}", "\n".join(lines))
                .replace("{{DOCUMENT_TYPE}}", document_type))


def _load(path: Path) -> Prompt:
    body = path.read_text(encoding="utf-8")
    m = PATTERN.match(path.name)
    assert m, path
    return Prompt(version=f"extract_{m.group(1)}", text=body, sha256=hashlib.sha256(body.encode()).hexdigest(), path=path)


def all_prompts() -> list[Prompt]:
    prompts = [_load(p) for p in sorted(PROMPT_DIR.glob("extract_v*.md")) if PATTERN.match(p.name)]
    return sorted(prompts, key=lambda p: int(re.search(r"v(\d+)", p.version).group(1)))


def get(version: str | None = None) -> Prompt:
    prompts = all_prompts()
    if not prompts:
        raise FileNotFoundError(f"no prompt files in {PROMPT_DIR}")
    if version is None:
        return prompts[-1]
    wanted = version.split("@", 1)[0]
    for p in prompts:
        if p.version == wanted:
            return p
    raise KeyError(f"unknown prompt version {version!r}; have {[p.version for p in prompts]}")
