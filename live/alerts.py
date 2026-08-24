from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
@dataclass(frozen=True,slots=True)
class Alert:
    key:str; message:str; priority:int=1
class AlertPriority(IntEnum): NORMAL=1; IMPORTANT=2; CRITICAL=3
class AlertEngine:
    def __init__(self): self._sent:set[str]=set()
    def emit(self,alert:Alert)->Alert|None:
        if alert.key in self._sent:return None
        self._sent.add(alert.key); return alert
    def reset(self,key:str|None=None)->None:
        if key is None:self._sent.clear()
        else:self._sent.discard(key)
