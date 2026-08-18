# Customer Email Agent

A beginner-friendly command-line application that uses the OpenRouter Chat Completions API to summarize customer emails and draft professional replies.

## Features

- Accepts email text directly or reads it from a text file.
- Uses a configurable OpenRouter-supported language model.
- Produces a concise summary and empathetic customer reply.
- Processes multiple emails in one session.
- Stores results locally in `data/customer_emails.json`.
- Provides a menu for processing emails, viewing stored emails, and exiting.
- Does not store API credentials in customer-email data.
- Instructs the model not to invent policies, refunds, timelines, actions, or other facts.

## Requirements

- Python 3.10 or newer
- An OpenRouter API key
- Internet access when processing an email

## Installation

From this project directory, optionally create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Configure `.env`

Copy `.env.example` to `.env` if needed, then set the values:

```text
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=your_model_name
```

Use a valid model ID available through OpenRouter. Never commit `.env`; it is included in `.gitignore`.

## Run the application

```powershell
python app.py
```

The application displays:

```text
1. Process Customer Email
2. View Stored Emails
3. Exit
```

## Process an email from the terminal

Select option `1`, then paste the email as a single input. For example:

```text
My payment appears to have failed, but I can see a pending amount. Please help.
```

Press Enter to submit it.

## Process an email from a text file

Create a text file such as `customer_email.txt`, then select option `1` and enter its path:

```text
customer_email.txt
```

Absolute Windows paths are also supported.

## Stored emails

Each successful result is appended to `data/customer_emails.json` with:

- `original_email`
- `summary`
- `generated_reply`
- `timestamp`

The API key and model credentials are not written to this file. Select option `2` to view stored records. The JSON file remains available across application runs.

## Example usage

1. Start the application with `python app.py`.
2. Select `1`.
3. Enter an email or text-file path.
4. Review the original email, summary, and generated reply.
5. Process another email or select `2` to view saved records.
6. Select `3` to exit.

## Troubleshooting

- **Missing API key:** Ensure `.env` exists and contains a real `OPENROUTER_API_KEY`.
- **Invalid model:** Set `OPENROUTER_MODEL` to a valid model ID available on OpenRouter.
- **HTTP/API error:** Check the API key, model availability, account credits, and OpenRouter status.
- **Network error:** Check internet connectivity and try again.
- **File not found:** Verify the text-file path and spelling.
- **Invalid stored JSON:** Back up and repair or replace `data/customer_emails.json` with `[]`.
- **Do not share credentials:** Never paste your API key into source code, customer email data, or version control.
