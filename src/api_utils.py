from __future__ import annotations
import requests
from typing import List, Dict, Any

BASE = "https://clinicaltrials.gov/api/v2"

def ping_version() -> Dict[str, Any]:
    r = requests.get(f"{BASE}/version", timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_trials_raw(term: str, page_size: int = 10) -> List[Dict[str, Any]]:
    params = {
        "format": "json",
        "query.term": term,
        "pageSize": page_size,
        # no 'fields' here — full payload
    }
    r = requests.get(f"{BASE}/studies", params=params, timeout=30)
    if r.status_code != 200:
        # log server message to see exactly why in the future
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.text}", response=r)
    r.raise_for_status()
    return r.json().get("studies", [])

def extract_brief(study: Dict[str, Any]) -> Dict[str, Any]:
    ps = study.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    desc = ps.get("descriptionModule", {})
    elig = ps.get("eligibilityModule", {})
    contacts = ps.get("contactsLocationsModule", {})

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "overall_status": ps.get("statusModule", {}).get("overallStatus"),
        "conditions": ps.get("conditionsModule", {}).get("conditions", []),
        "summary": desc.get("briefSummary", ""),
        "eligibility": elig.get("eligibilityCriteria", ""),
        "phase": ps.get("designModule", {}).get("phases"),
        "study_type": ps.get("designModule", {}).get("studyType"),
        "primary_purpose": ps.get("designModule", {}).get("designInfo", {}).get("primaryPurpose"),
        "locations": contacts.get("locations", []),  # list of dicts
        "start_date": ps.get("statusModule", {}).get("startDateStruct", {}),
        "completion_date": ps.get("statusModule", {}).get("completionDateStruct", {}),
    }

def search_trials_patient_friendly(
    condition: str,
    state_or_country: str | None = None,
    limit: int = 10,
    prefer_recruiting: bool = True,
) -> List[Dict[str, Any]]:
    term_parts = [condition]
    if state_or_country:
        term_parts.append(state_or_country)
    # don't add "Recruiting" to the term; we'll filter it manually instead
    term = " ".join(term_parts)

    studies = fetch_trials_raw(term=term, page_size=limit * 4)
    briefs = [extract_brief(s) for s in studies]

    # Filter for recruiting only
    recruiting_only = []
    for b in briefs:
        status = (b.get("overall_status") or "").upper().strip()
        if status == "RECRUITING":
            recruiting_only.append(b)

    # Prioritize by location
    if state_or_country:
        def score(b):
            locs = b.get("locations") or []
            return any(
                (state_or_country.lower() in (loc.get("state", "") or "").lower())
                or (state_or_country.lower() in (loc.get("country", "") or "").lower())
                for loc in locs
            )
        recruiting_only.sort(key=score, reverse=True)

    # Limit the number of results
    return recruiting_only[:limit]
