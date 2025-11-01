# Clinical Trial Agent (MVP)

Minimal prototype that:

- Asks 3–4 questions (condition, age, location, number of results)
- Queries ClinicalTrials.gov v2 API
- Summarizes results via course's LiteLLM proxy (or a direct fallback)

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
