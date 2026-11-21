"""Provider registry. One interface, three providers, ``rules`` always available."""
from __future__ import annotations

import os
from typing import Any

from .ollama import OllamaProvider
from .rules import RulesProvider

PROVIDER_NAMES = ("rules", "ollama")


def get_provider(name: str):
    name = (name or "auto").lower()
    if name == "rules":
        return RulesProvider()
    if name == "ollama":
        return OllamaProvider(model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct"))
    raise KeyError(f"unknown provider {name!r}; choose from {', '.join(PROVIDER_NAMES)} or auto")


def resolve(name: str) -> str:
    """Map ``auto`` to Ollama when it is usable, else to the offline rules provider."""
    if name and name.lower() != "auto":
        return name.lower()
    ok, _ = OllamaProvider(model=os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")).available()
    return "ollama" if ok else "rules"


def describe() -> list[dict[str, Any]]:
    out = []
    for name in PROVIDER_NAMES:
        p = get_provider(name)
        ok, reason = p.available()
        out.append({
            "name": name,
            "model": p.model,
            "available": ok,
            "reason": reason,
            "paid": p.paid,
        })
    return out
