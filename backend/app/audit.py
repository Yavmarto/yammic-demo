"""Hash-chained, append-only audit log. Call `record` inside the business transaction."""
import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import text

GENESIS = "0" * 64
FIELDS = ("ts", "actor", "role", "action", "entity_type", "entity_id", "participant_id",
          "before", "after", "source", "model", "prompt_version")


def _canon(d: dict) -> str:
    return json.dumps({k: d[k] for k in FIELDS}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def _hash(prev: str, d: dict) -> str:
    return hashlib.sha256((prev + _canon(d)).encode()).hexdigest()


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat()


def record(c, user, action, entity_type, entity_id, *, participant_id=None, before=None,
           after=None, source="human", model=None, prompt_version=None, actor=None, role=None):
    c.execute(text("SELECT pg_advisory_xact_lock(7743)"))  # serialise chain appends
    prev = c.execute(text("SELECT hash FROM audit_event ORDER BY seq DESC LIMIT 1")).scalar() or GENESIS
    ev = dict(ts=_iso(datetime.now(UTC)), actor=actor or user["username"], role=role or user["role"],
              action=action, entity_type=entity_type, entity_id=str(entity_id),
              participant_id=participant_id, before=before, after=after, source=source,
              model=model, prompt_version=prompt_version)
    # round-trip through JSON so the hashed form equals what Postgres jsonb returns
    ev["before"], ev["after"] = (json.loads(json.dumps(x, default=str)) for x in (before, after))
    c.execute(text("""INSERT INTO audit_event (ts, actor, role, action, entity_type, entity_id,
        participant_id, before, after, source, model, prompt_version, prev_hash, hash)
        VALUES (:ts, :actor, :role, :action, :entity_type, :entity_id, :participant_id,
        CAST(:before AS jsonb), CAST(:after AS jsonb), :source, :model, :prompt_version, :prev, :hash)"""),
              {**ev, "before": json.dumps(ev["before"]), "after": json.dumps(ev["after"]),
               "prev": prev, "hash": _hash(prev, ev)})


def verify(c) -> dict:
    prev, n = GENESIS, 0
    rows = c.execute(text("SELECT * FROM audit_event ORDER BY seq")).mappings()
    for r in rows:
        n += 1
        d = dict(r)
        d["ts"] = _iso(d["ts"])
        if d["prev_hash"] != prev:
            return {"ok": False, "count": n, "brokenSeq": d["seq"], "reason": "prev_hash does not match the previous event (event removed or reordered)"}
        if _hash(prev, d) != d["hash"]:
            return {"ok": False, "count": n, "brokenSeq": d["seq"], "reason": "hash does not match event content (event modified)"}
        prev = d["hash"]
    return {"ok": True, "count": n, "brokenSeq": None, "reason": None, "headHash": prev}
