from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from src.api_utils import ping_version, search_trials_patient_friendly
from src.llm_client import get_lm

load_dotenv()
lm = get_lm(model_name="gpt-4.1-mini", temperature=0.2, max_tokens=250)

def ask(prompt: str, default: str = "") -> str:
    txt = input(f"{prompt}: ").strip()
    return txt or default

def format_trials(trials: List[Dict], max_summary_chars: int | None = None) -> str:
    lines = []
    for i, t in enumerate(trials, 1):
        title = t.get("title") or "Untitled Study"
        nct = t.get("nct_id") or "N/A"
        status = (t.get("overall_status") or "Unknown").upper()
        conditions = ", ".join(t.get("conditions") or ["Not specified"])

        summary = (t.get("summary") or "").replace("\n", " ").strip()
        if max_summary_chars is not None:
            summary = summary[:max_summary_chars] + ("..." if len(summary) > max_summary_chars else "")

        block = (
            f"{i}. {title} (NCT: {nct})\n"
            f"   Status: {status}\n"
            f"   Conditions: {conditions}\n"
            f"   Summary: {summary}\n"
        )
        lines.append(block)
    return "\n".join(lines)



def summarize_for_user(age: str, condition: str, location: str, trials_block: str) -> str:
    prompt = (
        "You are a concise, empathetic assistant helping a patient discover clinical trials.\n"
        f"Patient: age {age}, condition '{condition}', location '{location}'.\n"
        "Write one short, friendly paragraph (5–7 sentences) summarizing what we found and next steps. "
        "Do NOT list or repeat the trials — I will print the full list after your paragraph. "
        "Remind the patient this is informational, not medical advice.\n"
    )
    text, _meta = lm(prompt)
    return text


def main():
    ver = ping_version()
    print(f"Connected to ClinicalTrials.gov API v{ver.get('apiVersion')} (data snapshot {ver.get('dataTimestamp')})\n")

    print("Hi! I’ll ask a few quick questions to find relevant clinical trials.\n")
    condition = ask("What condition are you looking for trials for?", "breast cancer")
    age = ask("How old are you?", "50")
    location = ask("Where are you located? (state or country)", "California")
    max_trials = ask("How many trial options would you like to see? (1–10)", "6")
    try:
        max_trials = int(max_trials)
        if max_trials < 1:
            print("Number must be at least 1 — using 1.")
            max_trials = 1
        elif max_trials > 10:
            print("Maximum is 10 trials — using 10.")
            max_trials = 10
    except ValueError:
        print("Invalid input — using default of 6.")
        max_trials = 6

    trials = search_trials_patient_friendly(
        condition=condition,
        state_or_country=location,
        limit=max_trials,
        prefer_recruiting=True,
    )

    if not trials:
        print("\nSorry—I couldn’t find trials with those inputs. Try broadening the condition or location.")
        return

    block = format_trials(trials, max_summary_chars=None)

    # 1) LLM paragraph only
    print("\n" + summarize_for_user(age, condition, location, block))

    # 2) Full, numbered list (all trials, full wording)
    print("\nHere are the trials we found:\n")
    print(block)

    outdir = Path("data"); outdir.mkdir(exist_ok=True, parents=True)
    (outdir / "last_query.txt").write_text(
        f"age={age}\ncondition={condition}\nlocation={location}\n\n{block}",
        encoding="utf-8"
    )
    print("\nSaved results to data/last_query.txt")

if __name__ == "__main__":
    main()
