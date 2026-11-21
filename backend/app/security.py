import hashlib
import hmac
import os
import time

import jwt
from fastapi import Depends, HTTPException, Query, Request

SECRET = os.environ.get("JWT_SECRET", "")
if len(SECRET) < 32:  # fail closed: no committed default; `make` generates one into ops/.env.local
    raise RuntimeError("JWT_SECRET missing or shorter than 32 chars (run via make, or set it)")
TTL = 8 * 3600
ITER = 60_000


def hash_password(pw: str) -> str:
    salt = os.urandom(8).hex()
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), ITER).hex()}"


def check_password(pw: str, stored: str) -> bool:
    salt, h = stored.split("$")
    return hmac.compare_digest(
        hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), ITER).hex(), h)


def make_token(username: str, role: str, name: str) -> str:
    return jwt.encode({"sub": username, "role": role, "name": name,
                       "exp": int(time.time()) + TTL}, SECRET, algorithm="HS256")


def current_user(request: Request, access_token: str | None = Query(None, include_in_schema=False)):
    h = request.headers.get("authorization", "")
    tok = h[7:] if h.lower().startswith("bearer ") else access_token  # query token: SSE clients
    if not tok:
        raise HTTPException(401, "Missing bearer token")
    try:
        p = jwt.decode(tok, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    return {"username": p["sub"], "role": p["role"], "name": p["name"]}


def require(*roles: str):
    def dep(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, f"Role '{user['role']}' may not do this (needs {', '.join(roles)})")
        return user
    return dep
