"""Minimal HTTP client for the AI service.

The AI service never opens the database. It logs in as the ``ai`` service user
and uses the same public REST API as the Flutter app. ``urllib`` keeps the
service dependency-free and works on a stock Python 3.12.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE = os.environ.get("YAMICC_API_URL", "http://localhost:8000").rstrip("/")


class ApiError(RuntimeError):
    def __init__(self, status: int, body: str, path: str):
        super().__init__(f"{status} {path}: {body[:300]}")
        self.status = status
        self.body = body
        self.path = path


class HttpApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE, username: str = "ai", password: str = "demo"):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: str | None = None

    # -- plumbing ---------------------------------------------------------
    def _request(self, method: str, path: str, payload: Any | None = None) -> Any:
        url = self.base_url + path
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                body = res.read().decode()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            raise ApiError(exc.code, exc.read().decode(errors="replace"), path) from exc
        except urllib.error.URLError as exc:
            raise ApiError(0, f"API not reachable at {self.base_url}: {exc}", path) from exc

    def login(self) -> None:
        data = self._request("POST", "/auth/login", {"username": self.username, "password": self.password})
        self.token = data["accessToken"]

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        if not self.token:
            self.login()
        try:
            return self._request(method, path, payload)
        except ApiError as exc:
            if exc.status == 401:  # token expired
                self.token = None
                self.login()
                return self._request(method, path, payload)
            raise

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, payload: Any) -> Any:
        return self.request("POST", path, payload)

    def patch(self, path: str, payload: Any) -> Any:
        return self.request("PATCH", path, payload)

    # -- domain helpers ---------------------------------------------------
    def queued_runs(self) -> list[dict]:
        return self.get("/runs?status=queued")

    def get_run(self, run_id: int) -> dict:
        return self.get(f"/runs/{run_id}")

    def get_document(self, document_id: str) -> dict:
        return self.get(f"/documents/{document_id}")

    def documents(self, participant_id: str) -> list[dict]:
        return self.get(f"/participants/{participant_id}/documents")

    def ecrf_fields(self, participant_id: str) -> list[dict]:
        return self.get(f"/participants/{participant_id}/ecrf")["fields"]

    def update_run(self, run_id: int, payload: dict) -> dict:
        return self.patch(f"/runs/{run_id}", payload)

    def post_extractions(self, run_id: int, payloads: list[dict]) -> list[dict]:
        return self.post(f"/runs/{run_id}/extractions", payloads)
