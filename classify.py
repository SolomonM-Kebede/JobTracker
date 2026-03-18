"""
Bilingual EN/DE keyword classifier with extended field extraction.
Extracts: label, company, job_title, department, sent_date, deadline, ad_link, documents, urgency.
"""

import re

# Keyword rules (order matters — first match wins) 

RULES = [
    {
        "label": "Job Offer",
        "urgency": "High",
        "keywords": [
            "pleased to offer", "offer of employment", "formal offer",
            "we'd like to offer", "we would like to offer", "congratulations.*offer",
            "offer letter", "starting salary", "compensation package",
            "vertragsangebot", "arbeitsangebot", "wir.*freude.*anbieten",
            "angebot.*stelle", "hiermit.*angebot", "einstellungszusage",
            "herzlichen.*wunsch.*stelle", "wir.*einstellen",
            "gehalt.*angebot", "anstellungsvertrag",
        ],
        "action": "Review offer and respond by deadline."
    },
    {
        "label": "Interview Invite",
        "urgency": "High",
        "keywords": [
            "invite you to interview", "schedule.*interview", "interview.*schedule",
            "would like to.*interview", "interview invitation", "book.*interview",
            "arrange.*interview", "next step.*interview", "interview.*next step",
            "please select.*time", "calendly", "when are you available",
            "vorstellungsgesprach", "vorstellungsgespräch",
            "einladung.*gesprach", "einladung.*gespräch",
            "gesprach.*einladung", "gespräch.*einladung",
            "zu einem gesprach einladen", "interview.*einladen",
            "einladung.*interview", "kennenlerngespräch",
            "vorstellungstermin", "telefoninterview",
            "videointerv", "teams.*gesprach", "zoom.*gesprach",
            "mochten.*kennenlernen", "möchten.*kennenlernen",
            "wann.*verfugbar", "wann.*verfügbar", "terminvereinbarung",
        ],
        "action": "Book your interview slot ASAP."
    },
    {
        "label": "Assessment/Task",
        "urgency": "High",
        "keywords": [
            "take-home", "coding challenge", "technical test", "technical assessment",
            "online test", "aptitude test", "complete.*task", "assignment",
            "hackerrank", "codility", "testgorilla", "pymetrics",
            "complete the following", "skill.*assessment",
            "testaufgabe", "probeaufgabe", "arbeitsaufgabe",
            "online.*test", "eignungstest", "assessment.?center", "ac-einladung",
            "coding.*aufgabe", "programmieraufgabe", "fahigkeitstest", "fähigkeitstest",
        ],
        "action": "Complete and submit the assessment."
    },
    {
        "label": "Follow-up Needed",
        "urgency": "Medium",
        "keywords": [
            "please reply", "kindly respond", "waiting for your response",
            "confirm your availability", "let us know", "get back to us",
            "respond by", "reply by", "awaiting your confirmation",
            "bitte antworten", "bitte melden", "bitte.*ruckmeldung", "bitte.*rückmeldung",
            "wir bitten um antwort", "teilen sie uns mit", "bitte bestatigen", "bitte bestätigen",
            "bis wann.*ruckmeldung", "warten auf ihre antwort",
            "bitte.*kontaktieren", "ruckantwort erbeten", "rückantwort erbeten",
        ],
        "action": "Reply to this email."
    },
    {
        "label": "Rejection",
        "urgency": "Low",
        "keywords": [
            "unfortunately", "regret to inform", "not moving forward",
            "decided to move forward with other", "not selected", "unsuccessful",
            "position has been filled", "will not be moving", "other candidates",
            "did not match", "does not meet", "no longer considering",
            "we won't be", "we will not be", "not taken forward",
            "leider", "absage", "mussen.*absagen", "müssen.*absagen",
            "nicht.*berucksichtigen", "nicht.*berücksichtigen",
            "haben.*entschieden.*anderen", "andere kandidaten",
            "nicht.*profil", "entspricht.*nicht",
            "konnten.*nicht uberzeugen", "konnten.*nicht überzeugen",
            "verzichten.*bewerbung", "stelle.*besetzt",
            "bedauern.*mitteilen", "negativ.*bescheid",
            "nicht.*einladen", "nicht weiterverfolgen",
        ],
        "action": "None"
    },
    {
        "label": "Application Confirmed",
        "urgency": "Low",
        "keywords": [
            "application received", "thank you for applying", "thank you for your application",
            "successfully submitted", "application has been received",
            "we have received your", "application confirmation",
            "received your application",
            "bewerbung.*erhalten", "bewerbung.*eingegangen", "eingang.*bewerbung",
            "danke.*bewerbung", "vielen dank.*bewerbung",
            "bestatigung.*bewerbung", "bestätigung.*bewerbung",
            "bewerbung.*bestatigt", "bewerbung.*bestätigt",
            "ihre unterlagen.*erhalten", "wir haben ihre bewerbung",
            "erfolgreich.*beworben",
        ],
        "action": "None — wait for next steps."
    },
]

# These indicate submitted application (outbound confirmation)
SENT_KEYWORDS = [
    # English
    "you have successfully applied", "your application was submitted",
    "successfully submitted your application", "application submitted",
    "you applied for", "your application for", "application complete",
    "you have applied", "submission confirmed", "form submitted",
    # German
    "sie haben sich.*beworben", "ihre bewerbung wurde.*abgeschickt",
    "bewerbung erfolgreich.*abgeschickt", "bewerbung wurde.*übermittelt",
    "bewerbung abgeschlossen", "bewerbung eingereicht",
    "sie haben sich erfolgreich beworben", "formular.*gesendet",
    "ihre bewerbung.*abgesendet",
]

AWAITING_KEYWORDS = [
    "application", "applied for", "position of", "role of",
    "vacancy", "job application", "we will be in touch",
    "under review", "reviewing applications", "hiring process",
    "bewerbung", "beworben", "stellenanzeige", "stellenangebot",
    "kandidatur", "bewerbungsverfahren", "auswahlverfahren",
    "wir melden uns", "prufen.*unterlagen", "prüfen.*unterlagen",
    "sichten.*bewerbungen",
]

#  Document type detection 
DOCUMENT_KEYWORDS = {
    "CV/Resume":        ["curriculum vitae", "lebenslauf", "resume", "cv"],
    "Cover Letter":     ["cover letter", "anschreiben", "motivationsschreiben"],
    "References":       ["references", "referenzen", "arbeitszeugnis", "zeugnis"],
    "Certificates":     ["certificate", "zertifikat", "abschluss", "diploma", "transcript"],
    "Portfolio":        ["portfolio", "work samples", "arbeitsproben"],
    "ID/Passport":      ["passport", "reisepass", "personalausweis", "identity"],
}

# Department/Area detection 

DEPARTMENT_KEYWORDS = {
    "Engineering":      ["engineer", "entwickler", "software", "backend", "frontend",
                         "fullstack", "devops", "it ", "tech", "informatik"],
    "Data/AI":          ["data", "machine learning", "ki ", "ai ", "analyst",
                         "data science", "künstliche intelligenz"],
    "Design":           ["design", "ux", "ui ", "creative", "grafik"],
    "Marketing":        ["marketing", "growth", "seo", "content", "social media"],
    "Finance":          ["finance", "finanz", "accounting", "buchhaltung", "controlling"],
    "HR":               ["human resources", "personalwesen", "hr ", "recruiting", "talent"],
    "Sales":            ["sales", "vertrieb", "account", "business development"],
    "Operations":       ["operations", "logistik", "supply chain", "projekt"],
    "Research":         ["research", "forschung", "wissenschaft", "r&d"],
    "Werkstudent":      ["werkstudent", "working student", "student assistant",
                         "studentische hilfskraft", "hiwi"],
    "Internship":       ["intern", "praktikum", "praktikant"],
}


def _match_any(text: str, patterns: list) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _extract_company(subject: str, sender_name: str) -> str:
    """
    Extract company name using this priority:
    1. sender_name directly (e.g. 'Siemens AG Recruiting', 'Acme Careers')
    2. Subject line: 'at <Company>' or 'bei <Firma>'
    """
    GENERIC_NAMES = {
        "noreply", "no reply", "no-reply", "donotreply", "do not reply",
        "notifications", "info", "careers", "jobs", "recruiting", "hr",
        "bewerbung", "talent", "recruitment", "linkedin", "xing", "stepstone",
        "indeed", "glassdoor", "arbeitsagentur", "support", "system",
    }

    if sender_name and len(sender_name) > 1:
        # Skip if looks like a raw email address (contains @ or starts with no-)
        if "@" not in sender_name and not re.match(r"no[- ]?reply", sender_name, re.IGNORECASE):
            # Strip noise suffixes: "Siemens AG Recruiting" -> "Siemens AG"
            cleaned = re.split(
                r"\s*[-|·–]\s*|\s+(?:careers|recruiting|hr|jobs|team|bewerbung|talent)$",
                sender_name, flags=re.IGNORECASE
            )[0].strip()

            if cleaned.lower() not in GENERIC_NAMES and len(cleaned) > 1:
                return cleaned

    # Fallback 1 — English: "Software Engineer at Acme Corp"
    match = re.search(r"\bat\s+([A-Z][a-zA-Z\s&.]+?)(?:\s*[-,!.]|$)", subject)
    if match:
        return match.group(1).strip()

    # Fallback 2 — German: "Entwickler bei Siemens AG"
    match = re.search(r"\b(?:bei|für)\s+([A-ZÄÖÜ][a-zA-ZäöüÄÖÜß\s&.]+?)(?:\s*[-,!.]|$)", subject)
    if match:
        return match.group(1).strip()

    return "Unknown"


def _extract_job_title(subject: str) -> str:
    patterns = [
        r"(?:for|re:|application for|applying for)\s+(?:the\s+)?(.+?)(?:\s+at\s+|\s*$)",
        r"(?:position|role|vacancy|job)[:\s]+(.+?)(?:\s+at\s+|\s*[-,]|\s*$)",
        r"(?:stelle als|position als|job als|bewerbung als|als)\s+(.+?)(?:\s+bei\s+|\s*[-,|]|\s*$)",
        r"(?:für die stelle|für die position)[:\s]+(.+?)(?:\s+bei\s+|\s*[-,]|\s*$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            title = match.group(1).strip().rstrip(".,!-")
            if 2 < len(title) < 60:
                return title.title()
    return "Unknown"


def _extract_department(subject: str, preview: str) -> str:
    """Detect department/area from subject and preview."""
    text = f"{subject} {preview}".lower()
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return dept
    return "Unknown"


def _extract_documents(preview: str) -> str:
    """Detect which documents were mentioned in the email."""
    text = preview.lower()
    found = []
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(doc_type)
    return ", ".join(found) if found else "Not specified"


def _extract_deadline(preview: str) -> str:
    """Try to extract a deadline date from email preview."""
    patterns = [
        # English: by March 15, by 15/03/2026
        r"by\s+(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"by\s+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
        r"deadline[:\s]+(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"deadline[:\s]+([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})",
        r"respond by[:\s]+(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        # German: bis zum 15. März 2026, bis 15.03.2026
        r"bis\s+(?:zum\s+)?(\d{1,2}\.\s*[A-Za-zäöüÄÖÜ]+\s+\d{4})",
        r"bis\s+(?:zum\s+)?(\d{1,2}\.\d{1,2}\.\d{2,4})",
        r"bewerbungsschluss[:\s]+(\d{1,2}\.\d{1,2}\.\d{2,4})",
        r"frist[:\s]+(\d{1,2}\.\d{1,2}\.\d{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, preview, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extract_ad_link(preview: str) -> str:
    """Try to extract job advertisement URL from email preview."""
    patterns = [
        r"https?://(?:www\.)?(?:stepstone|indeed|linkedin|xing|karriere|jobs|arbeitsagentur)"
        r"[^\s\"'<>]+",
        r"(?:job.*?link|stellenanzeige|advertisement|anzeige)[:\s]+(https?://[^\s\"'<>]+)",
        r"apply.*?(?:here|now)[:\s]*(https?://[^\s\"'<>]+)",
        r"(https?://[^\s\"'<>]{20,}(?:job|stelle|career|karriere|apply|bewerbung)[^\s\"'<>]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, preview, re.IGNORECASE)
        if match:
            return match.group(0) if "stepstone" in match.group(0) else match.group(1) \
                if match.lastindex and match.group(1) else match.group(0)
    return ""


def classify_email(subject: str, preview: str, sender: str = "", received: str = "") -> dict:
    """
    Classify a single email and extract all tracking fields.
    Returns full dict with label, company, job_title, department,
    documents, deadline, ad_link, urgency, action_needed.
    """
    combined = f"{subject} {preview}"
    sender_name = sender.split("<")[0].strip() if "<" in sender else sender
 
    # Extract fields regardless of label
    company    = _extract_company(subject, sender_name)
    job_title  = _extract_job_title(subject)
    department = _extract_department(subject, preview)
    documents  = _extract_documents(preview)
    deadline   = _extract_deadline(preview)
    ad_link    = _extract_ad_link(preview)
    sent_date  = received[:10] if received else ""
 
    base = {
        "company":              company,
        "job_title":            job_title,
        "department":           department,
        "documents":            documents,
        "sent_date":            sent_date,
        "deadline":             deadline,
        "ad_link":              ad_link,
        "notes":                "",
        "is_sent_application":  _match_any(combined, SENT_KEYWORDS) or _match_any(combined, ["application received", "bewerbung.*erhalten", "successfully submitted", "erfolgreich.*beworben"]),
    }
 
    for rule in RULES:
        if _match_any(combined, rule["keywords"]):
            label_match = rule["label"]  # noqa: F841
            return {
                **base,
                "label":         rule["label"],
                "urgency":       rule["urgency"],
                "summary":       f"{rule['label']} email regarding job application.",
                "action_needed": rule["action"],
                "confidence":    0.85,
            }
 
    if _match_any(combined, AWAITING_KEYWORDS):
        return {
            **base,
            "label":         "Awaiting Response",
            "urgency":       "Low",
            "summary":       "Job application email — no specific status detected.",
            "action_needed": "None — wait for response.",
            "confidence":    0.6,
        }
 
    return {
        **base,
        "label":         "Not Job Related",
        "urgency":       "Low",
        "summary":       "Does not match any job application patterns.",
        "action_needed": "None",
        "confidence":    0.5,
    }


def classify_batch(emails: list, **kwargs) -> list:
    results = []
    for i, email in enumerate(emails):
        print(f"🏷️  Classifying {i+1}/{len(emails)}: {email['subject'][:50]}...")
        # Pass "Name <email>" format so classify_email can extract sender_name cleanly
        sender_name  = email.get("sender_name", "").strip()
        sender_email = email.get("from", "").strip()
        sender_str   = f"{sender_name} <{sender_email}>" if sender_name else sender_email

        classification = classify_email(
            subject=email.get("subject", ""),
            preview=email.get("preview", ""),
            sender=sender_str,
            received=email.get("received", ""),
        )
        results.append({**email, **classification})
    return results


if __name__ == "__main__":
    tests = [
        ("Unfortunately we won't be moving forward", "We regret to inform you. Please submit CV and cover letter by 15.03.2026", "hr@company.com", "2026-02-01"),
        ("Interview Invitation - Software Engineer at Acme", "We'd like to invite you to interview. Please bring your portfolio.", "talent@acme.com", "2026-02-10"),
        ("Ihre Bewerbung als Werkstudent Informatik bei TechGmbH", "Vielen Dank für Ihre Bewerbung. Wir haben Ihre Unterlagen erhalten.", "jobs@techgmbh.de", "2026-01-15"),
        ("Absage - Data Analyst Position", "Leider müssen wir Ihnen mitteilen, dass wir andere Kandidaten bevorzugen.", "hr@firma.de", "2026-02-20"),
    ]
    print("=" * 65)
    for subject, preview, sender, received in tests:
        r = classify_email(subject, preview, sender, received)
        print(f"Subject   : {subject[:55]}")
        print(f"  Label   : {r['label']}")
        print(f"  Company : {r['company']}  |  Role: {r['job_title']}")
        print(f"  Dept    : {r['department']}  |  Docs: {r['documents']}")
        print(f"  Sent    : {r['sent_date']}  |  Deadline: {r['deadline'] or 'N/A'}")
        print()