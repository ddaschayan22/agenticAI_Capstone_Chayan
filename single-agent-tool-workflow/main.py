"""CLI entry point for the single-agent tool workflow."""

from __future__ import annotations

import json
from pathlib import Path

from agent import SingleAgent


ROOT = Path(__file__).resolve().parent


def main() -> None:
    agent = SingleAgent(ROOT)
    print("Enter the capstone requirement. Type 'exit' to quit.")
    while True:
        user_input = input("\nInput: ").strip()
        if user_input.lower() == "exit":
            return
        try:
            result = agent.run(user_input)
            print(f"\nGOALS\n{result.goals}")
            print(f"\nSUCCESS CRITERIA\n{result.success_criteria}")
            print(f"\nWORKFLOW\n{result.workflow}")
            print(f"\nTOOLS REQUIRED\n{result.tools_required}")
            print(f"\nTOOL DETAILS\n{result.tool_details}")
        except ValueError as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
