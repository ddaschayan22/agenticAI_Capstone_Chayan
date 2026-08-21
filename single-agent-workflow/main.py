"""Command-line entry point for the single-agent workflow."""

from __future__ import annotations

import json
from pathlib import Path

from agent import SingleAgent


ROOT = Path(__file__).resolve().parent


def main() -> None:
    agent = SingleAgent(ROOT)
    print("Single-Agent Workflow")
    print("Enter input text. Type 'exit' to quit.")
    while True:
        text = input("\nInput: ").strip()
        if text.lower() == "exit":
            print("Goodbye.")
            return
        try:
            result = agent.run(text)
            print(json.dumps(result.__dict__, indent=2, default=lambda value: value.__dict__))
        except ValueError as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
