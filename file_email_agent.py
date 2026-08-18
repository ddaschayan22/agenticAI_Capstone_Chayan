"""Process a customer email text file using the existing .env configuration."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_EMAIL_FILE = PROJECT_DIR / "email.txt"
DATA_FILE = PROJECT_DIR / "data" / "customer_emails.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class AgentError(Exception):
    """Expected error displayed without a traceback."""


def load_configuration() -> tuple[str, str]:
    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "").strip()

    if not api_key or api_key == "your_openrouter_api_key_here":
        raise AgentError("OPENROUTER_API_KEY is missing or contains the placeholder value.")
    if not model or model == "your_model_name":
        raise AgentError("OPENROUTER_MODEL is missing or contains the placeholder value.")
    return api_key, model


def read_email_file(file_path: Path) -> str:
    if not file_path.is_file():
        raise AgentError(f"Email file was not found: {file_path}")
    try:
        email = file_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise AgentError(f"Could not read email file: {exc}") from exc
    if not email:
        raise AgentError("The email file is empty.")
    return email


def parse_model_json(content: Any) -> dict[str, str]:
    if not isinstance(content, str):
        raise AgentError("The model returned no text content.")

    cleaned = content.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        result = json.loads(cleaned.strip())
    except json.JSONDecodeError as exc:
        raise AgentError("The model returned invalid JSON. Please try again.") from exc

    if not isinstance(result, dict):
        raise AgentError("The model response was not a JSON object.")
    if not isinstance(result.get("summary"), str) or not isinstance(result.get("reply"), str):
        raise AgentError("The model response must contain summary and reply text.")
    return {"summary": result["summary"].strip(), "reply": result["reply"].strip()}


def generate_response(email: str, api_key: str, model: str) -> dict[str, str]:
    system_message = (
        "You are a careful customer-support assistant. Use only the supplied email. "
        "Do not invent or assume company policies, refunds, compensation, order details, "
        "timelines, actions taken, promises, customer information, or product information. "
        "If information is missing, acknowledge that and politely request what is needed. "
        "Return only valid JSON with exactly these string fields: summary and reply. "
        "The summary must be concise. The reply must be professional, polite, empathetic, "
        "and helpful."
    )
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Customer email:\n---\n{email}\n---"},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost/customer-email-agent",
        "X-Title": "Customer Email File Agent",
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    except requests.RequestException as exc:
        raise AgentError(f"Network error while contacting OpenRouter: {exc}") from exc

    if response.status_code >= 400:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        raise AgentError(f"OpenRouter API error ({response.status_code}): {message}")

    try:
        content = response.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AgentError("OpenRouter returned an unexpected response format.") from exc
    return parse_model_json(content)


def save_result(email: str, summary: str, reply: str) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        records = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentError(f"Could not read stored email data: {exc}") from exc
    if not isinstance(records, list):
        raise AgentError("Stored email data must contain a JSON list.")

    records.append({
        "original_email": email,
        "summary": summary,
        "generated_reply": reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    try:
        DATA_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        raise AgentError(f"Could not save the result: {exc}") from exc


def main() -> None:
    file_path = PROJECT_DIR / "email.txt"
    print(f"Reading customer email from: {file_path}")
    try:
        email = read_email_file(file_path)
        api_key, model = load_configuration()
        print("Contacting OpenRouter. Please wait...")
        result = generate_response(email, api_key, model)
        print("\nORIGINAL CUSTOMER EMAIL\n-----------------------")
        print(email)
        print("\nSUMMARY\n-------")
        print(result["summary"])
        print("\nGENERATED REPLY\n----------------")
        print(result["reply"])
        save_result(email, result["summary"], result["reply"])
        print(f"\nSaved result to: {DATA_FILE}")
    except AgentError as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
