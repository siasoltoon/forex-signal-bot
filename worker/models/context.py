"""Lightweight repository context builder for agent prompts."""

from __future__ import annotations

from pathlib import Path


class ProjectContext:
    def __init__(self, root: str | Path, max_files: int = 300) -> None:
        self.root = Path(root).resolve()
        self.max_files = max_files

    def snapshot(self) -> str:
        files: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or ".git" in path.parts or ".venv" in path.parts or "__pycache__" in path.parts:
                continue
            files.append(str(path.relative_to(self.root)))
            if len(files) >= self.max_files:
                break
        return "Repository files:\n" + "\n".join(sorted(files))


__all__ = ["ProjectContext"]
