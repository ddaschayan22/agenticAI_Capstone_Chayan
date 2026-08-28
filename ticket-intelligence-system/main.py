from __future__ import annotations

import json
from orchestration.orchestrator import Orchestrator


def main() -> None:
    question = input("Ticket Intelligence question: ").strip()
    if not question:
        print("A question is required.")
        return
    print(json.dumps(Orchestrator().run(question), indent=2, default=str))


if __name__ == "__main__":
    main()
