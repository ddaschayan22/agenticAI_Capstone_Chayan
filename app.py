"""Customer email summarization and reply-generation CLI using OpenRouter."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "customer_emails.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class AgentError(Exception):
    """Expected application error with a user-friendly message."""


def load_configuration() -> tuple[str, str]:
    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "").strip()

    if not api_key or api_key == "your_openrouter_api_key_here":
        raise AgentError(
            "OPENROUTER_API_KEY is missing or still contains the placeholder. "
            "Add your key to the project's .env file."
        )
    if not model or model == "your_model_name":
        raise AgentError(
            "OPENROUTER_MODEL is missing or still contains the placeholder. "
            "Set a valid OpenRouter model in the project's .env file."
        )
    return api_key, model


def read_email_input(source: str) -> str:
    source = source.strip()
    if not source:
        raise AgentError("Customer email input cannot be empty.")

    possible_path = Path(source).expanduser()
    if possible_path.is_file():
        try:
            content = possible_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise AgentError(f"Could not read input file: {exc}") from exc
        if not content:
            raise AgentError("The input file is empty.")
        return content

    if any(character in source for character in '\\/:') and possible_path.suffix:
        raise AgentError(f"Input file was not found: {possible_path}")
    return source


def request_generation(api_key: str, model: str, email: str) -> tuple[str, str]:
    system_prompt = (
        "You are a careful customer-support assistant. Analyze only the customer "
        "email supplied by the user. Never invent policies, refunds, compensation, "
        "order details, timelines, actions, promises, or customer information. "
        "If necessary information is missing, explicitly say so and ask politely "
        "for the needed details. Return valid JSON with exactly two string fields: "
        "summary and reply. The summary must be concise. The reply must be "
        "professional, polite, empathetic, and helpful."
    )
    user_prompt = f"Customer email:\n---\n{email}\n---"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost/customer-email-agent",
        "X-Title": "Customer Email Agent",
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise AgentError(f"Network error while contacting OpenRouter: {exc}") from exc

    if response.status_code >= 400:
        try:
            details = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            details = response.text
        raise AgentError(f"OpenRouter returned HTTP {response.status_code}: {details}")

    try:
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AgentError("OpenRouter returned an unexpected response format.") from exc

    result = parse_model_json(content)
    return result["summary"], result["reply"]


def parse_model_json(content: Any) -> dict[str, str]:
    if not isinstance(content, str):
        raise AgentError("The model response did not contain text.")

    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AgentError("The model returned invalid JSON. Please try again.") from exc

    if not isinstance(parsed, dict) or not isinstance(parsed.get("summary"), str) or not isinstance(parsed.get("reply"), str):
        raise AgentError("The model response must contain string fields named summary and reply.")
    return {"summary": parsed["summary"].strip(), "reply": parsed["reply"].strip()}


def load_records() -> list[dict[str, str]]:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return []
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentError(f"Could not read stored email data: {exc}") from exc
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise AgentError("Stored email data must be a JSON list of records.")
    return raw


def save_record(email: str, summary: str, reply: str) -> None:
    records = load_records()
    records.append(
        {
            "original_email": email,
            "summary": summary,
            "generated_reply": reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    try:
        DATA_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        raise AgentError(f"Could not save email data: {exc}") from exc


def process_email() -> None:
    print("\nEnter the customer email text, or enter a path to a text file:")
    source = input("> ")
    email = read_email_input(source)
    api_key, model = load_configuration()
    print("\nContacting OpenRouter. Please wait...")
    summary, reply = request_generation(api_key, model, email)

    print("\nORIGINAL CUSTOMER EMAIL\n-----------------------")
    print(email)
    print("\nSUMMARY\n-------")
    print(summary)
    print("\nGENERATED REPLY\n----------------")
    print(reply)
    save_record(email, summary, reply)
    print(f"\nSaved to {DATA_FILE}")


def view_stored_emails() -> None:
    records = load_records()
    if not records:
        print("\nNo stored customer emails found.")
        return
    for number, record in enumerate(records, start=1):
        print(f"\nEMAIL {number} | {record.get('timestamp', 'Unknown timestamp')}")
        print("Original:", record.get("original_email", ""))
        print("Summary:", record.get("summary", ""))
        print("Reply:", record.get("generated_reply", ""))


def main() -> None:
    print("Customer Email Generation and Summarization Agent")
    while True:
        print("\n1. Process Customer Email")
        print("2. View Stored Emails")
        print("3. Exit")
        choice = input("Select an option: ").strip()
        try:
            if choice == "1":
                process_email()
            elif choice == "2":
                view_stored_emails()
            elif choice == "3":
                print("Goodbye.")
                return
            else:
                print("Please select 1, 2, or 3.")
        except AgentError as exc:
            print(f"\nError: {exc}")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")


if __name__ == "__main__":
    main()
