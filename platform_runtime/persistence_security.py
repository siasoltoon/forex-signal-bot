from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class StoredAnalysis:
    analysis_id: str
    user_id: str
    symbol: str
    decision: str
    confidence: float
    payload_json: str
    created_at: str


class SQLiteStore:
    def __init__(self, path: str | Path = "runtime.db") -> None:
        self.path = str(path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, language TEXT NOT NULL DEFAULT 'fa');
            CREATE TABLE IF NOT EXISTS analyses (analysis_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, symbol TEXT NOT NULL, decision TEXT NOT NULL, confidence REAL NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, job_type TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL, result_json TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS trades (trade_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, symbol TEXT NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_log (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, actor TEXT, payload_json TEXT NOT NULL, created_at TEXT NOT NULL);
            """)

    def save_analysis(self, analysis: StoredAnalysis) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO analyses VALUES (?, ?, ?, ?, ?, ?, ?)", (analysis.analysis_id, analysis.user_id, analysis.symbol, analysis.decision, analysis.confidence, analysis.payload_json, analysis.created_at))


class SecretManager:
    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_secret(secret: str, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.scrypt(secret.encode(), salt=salt, n=2**14, r=8, p=1)
        return f"{salt.hex()}:{digest.hex()}"

    @staticmethod
    def verify_secret(secret: str, encoded: str) -> bool:
        salt_hex, digest_hex = encoded.split(":", 1)
        expected = hashlib.scrypt(secret.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(expected.hex(), digest_hex)

    @staticmethod
    def sign_payload(payload: bytes, secret: bytes) -> str:
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: bytes) -> bool:
        return hmac.compare_digest(SecretManager.sign_payload(payload, secret), signature)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
