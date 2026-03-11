"""
fetch_emails.py — Parallel folder fetching for faster sync.
Fetches inbox, junk, and deleted simultaneously using threads.
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from auth import get_access_token

GRAPH_BASE      = "https://graph.microsoft.com/v1.0/me"
FOLDERS_TO_SCAN = ["inbox", "junkemail", "deleteditems"]
DATE_FILTER     = "2026-01-01T00:00:00Z"

JOB_KEYWORDS = [
    "application", "applied", "position", "role", "vacancy", "hiring",
    "interview", "offer", "unfortunately", "regret", "selected", "shortlisted",
    "assessment", "test", "task", "opportunity", "candidate", "recruitment",
    "thank you for applying", "we have reviewed", "next steps", "onboarding",
    # German
    "bewerbung", "stelle", "vorstellungsgesprach", "absage", "einladung",
    "leider", "beworben", "stellenangebot", "testaufgabe",
]


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _is_job_related(subject: str, body_preview: str) -> bool:
    text = (subject + " " + body_preview).lower()
    return any(kw in text for kw in JOB_KEYWORDS)


def _parse_email(email: dict, folder: str) -> dict:
    return {
        "id":          email.get("id"),
        "subject":     email.get("subject", "") or "",
        "preview":     email.get("bodyPreview", "") or "",
        "from":        email.get("from", {}).get("emailAddress", {}).get("address", ""),
        "sender_name": email.get("from", {}).get("emailAddress", {}).get("name", ""),
        "received":    email.get("receivedDateTime", ""),
        "folder":      folder,
        "is_read":     email.get("isRead", False),
    }


def fetch_folder(token: str, folder: str, max_emails: int = 100) -> list:
    """Fetch and filter one folder — runs in its own thread."""
    url = (
        f"{GRAPH_BASE}/mailFolders/{folder}/messages"
        f"?$top={max_emails}"
        f"&$select=id,subject,bodyPreview,from,receivedDateTime,isRead"
        f"&$orderby=receivedDateTime desc"
        f"&$filter=receivedDateTime ge {DATE_FILTER}"
    )

    raw, results = [], []
    while url:
        resp = requests.get(url, headers=_headers(token), timeout=15)
        if resp.status_code != 200:
            print(f"⚠️  Folder '{folder}': {resp.status_code}")
            break
        data = resp.json()
        raw.extend(data.get("value", []))
        url  = data.get("@odata.nextLink")

    for email in raw:
        parsed = _parse_email(email, folder)
        if _is_job_related(parsed["subject"], parsed["preview"]):
            results.append(parsed)

    print(f"   ✅ {folder}: {len(results)} job emails (of {len(raw)} total)")
    return results


def fetch_all_job_emails(max_per_folder: int = 100,
                          progress_cb=None) -> list:
    """
    Fetch all 3 folders IN PARALLEL — ~3x faster than sequential.
    progress_cb: optional callable(message) for Streamlit status updates.
    """
    def log(msg):
        print(msg)
        if progress_cb:
            progress_cb(msg)

    token = get_access_token()
    log("🔐 Authenticated — fetching folders in parallel...")

    all_emails = []

    # Run all 3 folder fetches simultaneously
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_folder, token, folder, max_per_folder): folder
            for folder in FOLDERS_TO_SCAN
        }
        for future in as_completed(futures):
            folder = futures[future]
            try:
                results = future.result()
                all_emails.extend(results)
            except Exception as e:
                log(f"⚠️  Error fetching {folder}: {e}")

    # Deduplicate by email id (in case of overlap)
    seen, deduped = set(), []
    for email in all_emails:
        if email["id"] not in seen:
            seen.add(email["id"])
            deduped.append(email)

    log(f"✅ {len(deduped)} job-related emails found across all folders.")
    return deduped


if __name__ == "__main__":
    emails = fetch_all_job_emails()
    for e in emails[:5]:
        print(f"\n📧 {e['subject'][:60]}")
        print(f"   From: {e['sender_name']} <{e['from']}>")
        print(f"   Date: {e['received'][:10]}")