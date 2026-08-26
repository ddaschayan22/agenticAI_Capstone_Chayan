"""Optional OpenRouter client for future planning extensions."""

from __future__ import annotations

from pathlib import Path


class OpenRouterClient:
    """Placeholder client; ticket planning is deterministic in this project."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def configured(self) -> bool:
        return False
