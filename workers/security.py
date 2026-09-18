from __future__ import annotations

import hashlib
import hmac


class JobAuthenticator:
    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("worker authentication secret is required")
        self._secret = secret.encode()

    def sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()

    def verify(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)
