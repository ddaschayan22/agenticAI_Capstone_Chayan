# Generic Capstone Planner Agent

A single-agent Python application that accepts any capstone requirement and generates goals, success criteria, workflow tasks, required tools, canonical tool details, goal-task-tool mappings, and JSON outcomes.

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Configure `.env` using `.env.example`, then run:

```powershell
python main.py
```

The OpenRouter temperature is `0.5`. The tool schemas remain consistent whenever a tool is reused; task-specific values belong in each task's parameter object.
