from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Locale:
    code: str
    name: str
    fallback: str = "en"


@dataclass(frozen=True, slots=True)
class LocalizedText:
    key: str
    values: dict[str, str]

    def resolve(self, language: str, fallback: str = "en") -> str:
        return self.values.get(language, self.values.get(fallback, self.key))


SUPPORTED_LOCALES = (Locale("fa", "فارسی", "en"), Locale("en", "English", "en"))

__all__ = ["Locale", "LocalizedText", "SUPPORTED_LOCALES"]
