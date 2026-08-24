from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import hmac

@dataclass(frozen=True, slots=True)
class AuthResult:
    authenticated: bool
    subject: str | None = None

class RequestAuthenticator:
    def __init__(self, secret: str) -> None:
        self._secret = secret.encode()
    def sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode(), sha256).hexdigest()
    def verify(self, payload: str, signature: str) -> AuthResult:
        expected = self.sign(payload)
        return AuthResult(hmac.compare_digest(expected, signature))
