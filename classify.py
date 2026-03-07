"""
 Keyword/Rule-based email classifier without LLM
Bilingual: matches English AND German job email patterns.
"""

import re

# Keyword rules 

RULES = [
    {
        "label": "Job Offer",
        "urgency": "High",
        "keywords": [
            # English
            "pleased to offer", "offer of employment", "formal offer",
            "we'd like to offer", "we would like to offer", "congratulations.*offer",
            "offer letter", "starting salary", "compensation package",
            # German
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
            # English
            "invite you to interview", "schedule.*interview", "interview.*schedule",
            "would like to.*interview", "interview invitation", "book.*interview",
            "arrange.*interview", "next step.*interview", "interview.*next step",
            "please select.*time", "calendly", "when are you available",
            # German
            "vorstellungsgesprach", "vorstellungsgespräch",
            "einladung.*gesprach", "einladung.*gespräch",
            "gesprach.*einladung", "gespräch.*einladung",
            "zu einem gesprach einladen", "interview.*einladen",
            "einladung.*interview", "kennenlerngespräch", "kennenlerngespräch",
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
            # English
            "take-home", "coding challenge", "technical test", "technical assessment",
            "online test", "aptitude test", "complete.*task", "assignment",
            "hackerrank", "codility", "testgorilla", "pymetrics",
            "complete the following", "skill.*assessment",
            # German
            "testaufgabe", "probeaufgabe", "arbeitsaufgabe",
            "online.*test", "eignungstest", "assessment.?center", "ac-einladung",
            "coding.*aufgabe", "programmieraufgabe", "fahigkeitstest", "fähigkeitstest",
            "bitte.*aufgabe.*losen", "bitte.*test.*abschliessen",
        ],
        "action": "Complete and submit the assessment."
    },
    {
        "label": "Follow-up Needed",
        "urgency": "Medium",
        "keywords": [
            # English
            "please reply", "kindly respond", "waiting for your response",
            "confirm your availability", "let us know", "get back to us",
            "respond by", "reply by", "awaiting your confirmation",
            # German
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
            # English
            "unfortunately", "regret to inform", "not moving forward",
            "decided to move forward with other", "not selected", "unsuccessful",
            "position has been filled", "will not be moving", "other candidates",
            "did not match", "does not meet", "no longer considering",
            "we won't be", "we will not be", "not taken forward",
            # German
            "leider", "absage", "mussen.*absagen", "müssen.*absagen",
            "nicht.*berucksichtigen", "nicht.*berücksichtigen",
            "haben.*entschieden.*anderen", "andere kandidaten",
            "nicht.*profil", "entspricht.*nicht", "konnten.*nicht uberzeugen", "konnten.*nicht überzeugen",
            "verzichten.*bewerbung", "stelle.*besetzt", "stellen.*besetzt",
            "bedauern.*mitteilen", "negativ.*bescheid", "kein.*interesse",
            "nicht.*einladen", "nicht weiterverfolgen",
        ],
        "action": "None"
    },
    {
        "label": "Application Confirmed",
        "urgency": "Low",
        "keywords": [
            # English
            "application received", "thank you for applying", "thank you for your application",
            "successfully submitted", "application has been received",
            "we have received your", "application confirmation",
            "received your application",
            # German
            "bewerbung.*erhalten", "bewerbung.*eingegangen", "eingang.*bewerbung",
            "danke.*bewerbung", "vielen dank.*bewerbung", "bestatigung.*bewerbung", "bestätigung.*bewerbung",
            "bewerbung.*bestatigt", "bewerbung.*bestätigt", "ihre unterlagen.*erhalten",
            "wir haben ihre bewerbung", "erfolgreich.*beworben",
        ],
        "action": "None — wait for next steps."
    },
]

AWAITING_KEYWORDS = [
    # English
    "application", "applied for", "position of", "role of",
    "vacancy", "job application", "we will be in touch",
    "under review", "reviewing applications", "hiring process",
    # German
    "bewerbung", "beworben", "stellenanzeige", "stellenangebot",
    "kandidatur", "bewerbungsverfahren", "auswahlverfahren",
    "wir melden uns", "prufen.*unterlagen", "prüfen.*unterlagen",
    "sichten.*bewerbungen",
]


def _match_any(text: str, patterns: list) -> bool:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _extract_company(subject: str, sender_email: str) -> str:
    if sender_email and "@" in sender_email:
        domain = sender_email.split("@")[-1]
        generic = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
            "noreply.com", "no-reply.com", "notifications.com",
            "stepstone.de", "xing.com", "linkedin.com", "indeed.com",
            "arbeitsagentur.de", "jobs.de", "karriere.de"
        }
        if domain not in generic:
            return domain.split(".")[0].replace("-", " ").title()

    # English
    match = re.search(r"\bat\s+([A-Z][a-zA-Z\s&]+?)(?:\s*[-,!.]|$)", subject)
    if match:
        return match.group(1).strip()

    # German
    match = re.search(r"\b(?:bei|für)\s+([A-ZÄÖÜ][a-zA-ZäöüÄÖÜß\s&]+?)(?:\s*[-,!.]|$)", subject)
    if match:
        return match.group(1).strip()

    return "Unknown"


def _extract_job_title(subject: str) -> str:
    patterns = [
        # English
        r"(?:for|re:|application for|applying for)\s+(?:the\s+)?(.+?)(?:\s+at\s+|\s*$)",
        r"(?:position|role|vacancy|job)[:\s]+(.+?)(?:\s+at\s+|\s*[-,]|\s*$)",
        # German
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


def classify_email(subject: str, preview: str, sender: str = "") -> dict:
    """Classify a single email. Returns dict with label, company, urgency, etc."""
    combined = f"{subject} {preview}"
    sender_email = sender.split("<")[-1].replace(">", "").strip() if "<" in sender else sender

    for rule in RULES:
        if _match_any(combined, rule["keywords"]):
            return {
                "label":         rule["label"],
                "company":       _extract_company(subject, sender_email),
                "job_title":     _extract_job_title(subject),
                "urgency":       rule["urgency"],
                "summary":       f"{rule['label']} email regarding job application.",
                "action_needed": rule["action"],
                "confidence":    0.85
            }

    if _match_any(combined, AWAITING_KEYWORDS):
        return {
            "label":         "Awaiting Response",
            "company":       _extract_company(subject, sender_email),
            "job_title":     _extract_job_title(subject),
            "urgency":       "Low",
            "summary":       "Job application email — no specific status detected.",
            "action_needed": "None — wait for response.",
            "confidence":    0.6
        }

    return {
        "label":         "Not Job Related",
        "company":       "Unknown",
        "job_title":     "Unknown",
        "urgency":       "Low",
        "summary":       "Does not match any job application patterns.",
        "action_needed": "None",
        "confidence":    0.5
    }


def classify_batch(emails: list, **kwargs) -> list:
    """Classify a list of emails. Returns list with classification fields added."""
    results = []
    for i, email in enumerate(emails):
        print(f"Classifying {i+1}/{len(emails)}: {email['subject'][:50]}...")
        classification = classify_email(
            subject=email.get("subject", ""),
            preview=email.get("preview", ""),
            sender=f"{email.get('sender_name', '')} <{email.get('from', '')}>"
        )
        results.append({**email, **classification})
    return results


if __name__ == "__main__":
    tests = [
        # English
        ("Unfortunately we won't be moving forward", "We regret to inform you...", "hr@company.com"),
        ("Interview Invitation - Software Engineer at Acme", "We'd like to invite you to interview", "talent@acme.com"),
        ("Your application for Backend Developer at TechCorp", "Thank you for applying", "noreply@techcorp.io"),
        ("Complete your Codility Assessment", "Please complete the coding challenge", "no-reply@codility.com"),
        ("Offer of Employment - Junior Developer", "We are pleased to offer you the position", "hr@startup.com"),
        # German
        ("Absage Ihrer Bewerbung als Werkstudent", "Leider müssen wir Ihnen mitteilen...", "hr@firma.de"),
        ("Einladung zum Vorstellungsgespräch bei Deutsche Bank", "Wir möchten Sie zu einem Gespräch einladen", "karriere@db.de"),
        ("Ihre Bewerbung ist eingegangen", "Vielen Dank für Ihre Bewerbung. Wir haben Ihre Unterlagen erhalten.", "jobs@bosch.de"),
        ("Testaufgabe für die Stelle als Python Entwickler", "Bitte lösen Sie die folgende Aufgabe", "hr@startup.de"),
        ("Vertragsangebot - Junior Softwareentwickler", "Wir freuen uns, Ihnen hiermit ein Angebot zu unterbreiten", "personal@siemens.de"),
    ]
    print("=" * 65)
    for subject, preview, sender in tests:
        r = classify_email(subject, preview, sender)
        flag = "de" if any(c in subject for c in "äöüÄÖÜß") or subject.endswith(".de") else "en"
        print(f"{flag} {subject[:55]}")
        print(f"   → {r['label']} | {r['company']} | {r['urgency']} urgency")
        print()