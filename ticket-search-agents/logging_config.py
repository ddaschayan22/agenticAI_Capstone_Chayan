"""Structured logs identifying planner and executor agents."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ticket_search_agents")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | agent_name=%(agent_name)s | agent_type=%(agent_type)s | %(levelname)s | %(message)s")
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger


class AgentLogAdapter(logging.LoggerAdapter):
    def process(self, message, kwargs):
        kwargs.setdefault("extra", {}).update(self.extra)
        return message, kwargs
