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
SCREENING_PATTERN = re.compile(r"^screening_(v\d+)\.md$")
PROTOCOL_PATTERN = re.compile(r"^protocol_(v\d+)\.md$")


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


def _load_named(path: Path, prefix: str, pattern: re.Pattern[str]) -> Prompt:
    body = path.read_text(encoding="utf-8")
    m = pattern.match(path.name)
    assert m, path
    return Prompt(
        version=f"{prefix}_{m.group(1)}",
        text=body,
        sha256=hashlib.sha256(body.encode()).hexdigest(),
        path=path,
    )


def get_screening_prompt(version: str | None = None) -> Prompt:
    prompts = [
        _load_named(p, "screening", SCREENING_PATTERN)
        for p in sorted(PROMPT_DIR.glob("screening_v*.md"))
        if SCREENING_PATTERN.match(p.name)
    ]
    if not prompts:
        raise FileNotFoundError(f"no screening prompt files in {PROMPT_DIR}")
    if version is None:
        return prompts[-1]
    wanted = version.split("@", 1)[0]
    for p in prompts:
        if p.version == wanted:
            return p
    raise KeyError(f"unknown screening prompt version {version!r}")


def get_protocol_prompt(version: str | None = None) -> Prompt:
    prompts = [
        _load_named(p, "protocol", PROTOCOL_PATTERN)
        for p in sorted(PROMPT_DIR.glob("protocol_v*.md"))
        if PROTOCOL_PATTERN.match(p.name)
    ]
    if not prompts:
        raise FileNotFoundError(f"no protocol prompt files in {PROMPT_DIR}")
    if version is None:
        return prompts[-1]
    wanted = version.split("@", 1)[0]
    for p in prompts:
        if p.version == wanted:
            return p
    raise KeyError(f"unknown protocol prompt version {version!r}")
