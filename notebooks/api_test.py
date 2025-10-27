import requests

BASE = "https://clinicaltrials.gov/api/v2"

def ping_version():
    r = requests.get(f"{BASE}/version", timeout=20)
    r.raise_for_status()
    return r.json()

def search_trials(term="breast cancer", limit=3):
    params = {
        "format": "json",
        "query.term": term,
        "pageSize": limit,
    }
    r = requests.get(f"{BASE}/studies", params=params, timeout=30)
    if r.status_code != 200:
        print("Error:", r.status_code, r.text)
        r.raise_for_status()
    data = r.json()
    studies = data.get("studies", [])
    for i, s in enumerate(studies, 1):
        id_mod = s["protocolSection"]["identificationModule"]
        desc = s["protocolSection"].get("descriptionModule", {})
        print(f"{i}. {id_mod.get('briefTitle')}")
        print(desc.get("briefSummary", "No summary."), "\n")

print(ping_version())
search_trials("breast cancer", 3)
