"""Guarded local repository tools for the coding agent.

The agent receives only these injected capabilities; no unrestricted shell is exposed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class RepositoryTools:
    def __init__(self, root: str | Path, max_read_bytes: int = 200_000) -> None:
        self.root = Path(root).resolve()
        self.max_read_bytes = max_read_bytes

    def _path(self, path: str) -> Path:
        candidate = (self.root / path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Path escapes repository root")
        return candidate

    def list_directory(self, path: str = ".") -> list[str]:
        target = self._path(path)
        if not target.is_dir():
            raise ValueError("Not a directory")
        return sorted(str(p.relative_to(self.root)) for p in target.iterdir())[:500]

    def read_file(self, path: str) -> str:
        target = self._path(path)
        if not target.is_file():
            raise FileNotFoundError(path)
        if target.stat().st_size > self.max_read_bytes:
            raise ValueError("File exceeds agent read limit")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if len(content.encode("utf-8")) > self.max_read_bytes:
            raise ValueError("File exceeds agent write limit")
        target.write_text(content, encoding="utf-8")
        return f"wrote {target.relative_to(self.root)}"

    def search_code(self, query: str) -> list[str]:
        if not query.strip():
            raise ValueError("query is required")
        matches: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path.stat().st_size > self.max_read_bytes:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if query in text:
                matches.append(str(path.relative_to(self.root)))
                if len(matches) >= 200:
                    break
        return matches

    def git_status(self) -> str:
        return self._git(["status", "--short"])

    def git_diff(self) -> str:
        return self._git(["diff", "--"])

    def run_tests(self, target: str = "tests") -> str:
        target_path = self._path(target)
        if not target_path.exists():
            raise FileNotFoundError(target)
        return self._run(["python", "-m", "pytest", target])

    def _git(self, args: list[str]) -> str:
        return self._run(["git", *args])

    def _run(self, args: list[str], timeout: int = 300) -> str:
        completed = subprocess.run(args, cwd=self.root, capture_output=True, text=True, timeout=timeout, shell=False)
        output = (completed.stdout + "\n" + completed.stderr).strip()
        if completed.returncode:
            raise RuntimeError(f"command failed ({completed.returncode}): {output[-12000:]}")
        return output[-12000:]


__all__ = ["RepositoryTools"]
