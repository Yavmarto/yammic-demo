"""Read-only workflow help for the local synthetic demo."""

import re
from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .security import require

router = APIRouter(prefix="/assistant", tags=["assistant"])
DEMO_USERS = Depends(require("nurse", "pi", "monitor"))
VERSION = "v0.9.1"
CATALOG = "https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json"

TOPICS = {
    "review": (
        "Review a suggestion",
        "Open AI review and select a suggestion. Compare its quote with the source before accepting, correcting, rejecting, or deferring it.",
        {"review", "evidence", "suggestion", "quote"},
    ),
    "manual": (
        "Enter a value manually",
        "In AI review, choose Enter from source. Select the field and document, enter the value, and include the exact quote.",
        {"manual", "blank", "missing", "abstain"},
    ),
    "export": (
        "Export checked data",
        "The principal investigator or monitor can open Export and choose a checked-data format such as ODM or FHIR.",
        {"export", "odm", "fhir", "download"},
    ),
    "retry": (
        "Retry an extraction",
        "In AI review, a nurse or principal investigator can retry a failed extraction. The app keeps the original run and reviewed values.",
        {"retry", "failed", "failure"},
    ),
}


class Prompt(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=32)
    surfaceId: str = Field(pattern=r"^workflow-help-[a-f0-9]{32}$")
    sourceComponentId: str = Field(max_length=48)
    timestamp: datetime
    context: dict[str, Literal["workflow_help"]] = Field(default_factory=dict, max_length=1)


class ActionMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["v0.9.1"]
    action: Action


def surface(answer: str) -> dict:
    surface_id = f"workflow-help-{uuid4().hex}"
    root = {"id": "root", "component": "Column", "children": ["answer"]}
    components = [root, {"id": "answer", "component": "Text", "text": answer}]
    for name, (label, _, _) in TOPICS.items():
        button_id = f"choose-{name}"
        label_id = f"label-{name}"
        root["children"].append(button_id)
        components.extend([
            {"id": label_id, "component": "Text", "text": label},
            {"id": button_id, "component": "Button", "child": label_id,
             "action": {"event": {"name": name, "context": {"kind": "workflow_help"}}}},
        ])
    return {"messages": [
        {"version": VERSION, "createSurface": {"surfaceId": surface_id, "catalogId": CATALOG}},
        {"version": VERSION, "updateComponents": {"surfaceId": surface_id, "components": components}},
    ]}


@router.post("/turn")
def turn(prompt: Prompt, user=DEMO_USERS):
    words = set(re.findall(r"[a-z]+", prompt.text.casefold()))
    if not words:
        raise HTTPException(422, "Enter a workflow question.")
    matches = [answer for _, answer, terms in TOPICS.values() if terms & words]
    answer = matches[0] if len(matches) == 1 else "Choose a topic for help with the fictional study workflow."
    return surface(answer)


@router.post("/action")
def action(message: ActionMessage, user=DEMO_USERS):
    event = message.action
    topic = TOPICS.get(event.name)
    if topic is None or event.sourceComponentId != f"choose-{event.name}" or event.context != {"kind": "workflow_help"}:
        raise HTTPException(422, "Choose an available workflow topic.")
    return surface(topic[1])
