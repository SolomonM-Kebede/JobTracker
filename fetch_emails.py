"""
fetch_emails.py — Fetch emails from ALL folders including Junk/Spam
Filters to emails received from 2026 onwards.
"""

import requests
from auth import get_access_token

GRAPH_BASE = "https://graph.microsoft.com/v1.0/me"

FOLDERS_TO_SCAN = ["inbox", "junkemail", "deleteditems"]

# Only fetch emails from this date onwards
DATE_FILTER = "2026-01-01T00:00:00Z"

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


def fetch_emails_from_folder(token: str, folder: str, max_emails: int = 100) -> list:
    """Fetch emails from a folder, filtered to DATE_FILTER onwards."""
    url = (
        f"{GRAPH_BASE}/mailFolders/{folder}/messages"
        f"?$top={max_emails}"
        f"&$select=id,subject,bodyPreview,from,receivedDateTime,isRead"
        f"&$orderby=receivedDateTime desc"
        f"&$filter=receivedDateTime ge {DATE_FILTER}"
    )

    emails = []
    while url:
        resp = requests.get(url, headers=_headers(token))
        if resp.status_code != 200:
            print(f"Could not fetch folder '{folder}': {resp.status_code} — {resp.text[:200]}")
            break

        data = resp.json()
        emails.extend(data.get("value", []))
        url = data.get("@odata.nextLink")

    return emails


def fetch_all_job_emails(max_per_folder: int = 100) -> list:
    """
    Fetches from all folders since 2026-01-01, filters job-related emails.
    Returns list of dicts ready for classification.
    """
    token = get_access_token()
    all_emails = []

    for folder in FOLDERS_TO_SCAN:
        print(f"Scanning folder: {folder} (from 2026)...")
        emails = fetch_emails_from_folder(token, folder, max_per_folder)
        print(f"   Found {len(emails)} emails since 2026, filtering for job-related...")

        for email in emails:
            subject = email.get("subject", "") or ""
            preview = email.get("bodyPreview", "") or ""

            if _is_job_related(subject, preview):
                all_emails.append({
                    "id":          email.get("id"),
                    "subject":     subject,
                    "preview":     preview,
                    "from":        email.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "sender_name": email.get("from", {}).get("emailAddress", {}).get("name", ""),
                    "received":    email.get("receivedDateTime", ""),
                    "folder":      folder,
                    "is_read":     email.get("isRead", False),
                })

    print(f"\n Total job-related emails found: {len(all_emails)}")
    return all_emails


if __name__ == "__main__":
    emails = fetch_all_job_emails()
    for e in emails[:5]:
        print(f"\n{e['subject'][:60]}")
        print(f"   From: {e['sender_name']} <{e['from']}>")
        print(f"   Date: {e['received'][:10]}")
        print(f"   Folder: {e['folder']}")