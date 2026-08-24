from __future__ import annotations
from dataclasses import dataclass
from time import sleep
from typing import Callable, TypeVar
T=TypeVar('T')
@dataclass(frozen=True,slots=True)
class RetryPolicy:
    attempts:int=3
    backoff_seconds:float=0.0
class Retrier:
    def __init__(self,policy:RetryPolicy|None=None): self.policy=policy or RetryPolicy()
    def run(self,fn:Callable[[],T])->T:
        last:Exception|None=None
        for i in range(max(1,self.policy.attempts)):
            try:return fn()
            except Exception as exc:
                last=exc
                if i+1<self.policy.attempts and self.policy.backoff_seconds>0:sleep(self.policy.backoff_seconds*(2**i))
        assert last is not None
        raise last
