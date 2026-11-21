"""Hash-chained, append-only audit log. Call `record` inside the business transaction."""
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.engine import Engine

GENESIS = "0" * 64
# HMAC key, kept outside the DB (ops/.env.local); anchor = append-only (count, head) log outside the DB
if len(os.environ.get("AUDIT_KEY", "")) < 32:
    raise RuntimeError("AUDIT_KEY missing or shorter than 32 chars (run via make, or set it)")
KEY = os.environ["AUDIT_KEY"].encode()
ANCHOR = Path(os.environ.get("AUDIT_ANCHOR") or Path(__file__).resolve().parents[2] / "ops" / "audit-anchor.log")
FIELDS = ("ts", "actor", "role", "action", "entity_type", "entity_id", "participant_id",
          "before", "after", "source", "model", "prompt_version")


def _canon(d: dict) -> str:
    return json.dumps({k: d[k] for k in FIELDS}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def _hash(prev: str, d: dict) -> str:
    return hmac.new(KEY, (prev + _canon(d)).encode(), hashlib.sha256).hexdigest()


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat()


@event.listens_for(Engine, "commit")
def _anchor_on_commit(conn):  # only committed events are anchored; rollbacks leave no line
    if p := conn.info.pop("audit_anchor", None):
        with ANCHOR.open("a") as f:
            f.write(f"{datetime.now(UTC).isoformat()} {p[0]} {p[1]}\n")


@event.listens_for(Engine, "rollback")
def _drop_pending(conn):
    conn.info.pop("audit_anchor", None)


def _anchors():
    """Every (count, head) line in the anchor log, or None if the log is missing."""
    try:
        return [(int(r[1]), r[2]) for r in (l.split() for l in ANCHOR.read_text().splitlines() if l.strip())]
    except FileNotFoundError:
        return None


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
    # ponytail: count(*) per write is O(n); fine at demo scale
    c.info["audit_anchor"] = (c.execute(text("SELECT count(*) FROM audit_event")).scalar(), _hash(prev, ev))


def verify(c) -> dict:
    prev, n, at = GENESIS, 0, {}
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
        at[n] = prev
    anchors = _anchors()
    if anchors is None and n:
        return {"ok": False, "count": n, "brokenSeq": None, "reason": "anchor log missing (cannot prove no events were deleted)"}
    # Check every anchor, not only the newest: a tail deletion followed by a normal app write
    # re-anchors the same count with a different head, which only the older line exposes.
    # ponytail: O(anchors) per verify; fine at demo scale, keep a checkpoint offset if the log grows large
    for cnt, head in anchors or ():
        if cnt > n:
            return {"ok": False, "count": n, "brokenSeq": None, "reason": f"events deleted from the end of the chain: anchor says {cnt} events"}
        if at[cnt] != head:
            return {"ok": False, "count": n, "brokenSeq": None, "reason": f"chain rewritten (does not match the external anchor at event {cnt})"}
    return {"ok": True, "count": n, "brokenSeq": None, "reason": None, "headHash": prev}
