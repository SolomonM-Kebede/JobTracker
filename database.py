"""
database.py — MongoDB Atlas storage for job application emails
Connection string is read from .env (MONGODB_URI)
"""

import os
from datetime import datetime, UTC 
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne, DESCENDING
from pymongo.errors import ConnectionFailure

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME     = "job_tracker"
COLLECTION  = "applications"

_client = None


def get_collection():
    """Return the MongoDB collection, creating the client once."""
    global _client
    if _client is None:
        if not MONGODB_URI:
            raise ValueError(
                "MONGODB_URI not set in .env\n"
                "   Get it from: MongoDB Atlas → Connect → Drivers → copy URI"
            )
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        try:
            _client.admin.command("ping")
            print("Connected to MongoDB Atlas.")
        except ConnectionFailure:
            raise ConnectionFailure("Could not connect to MongoDB Atlas. Check your MONGODB_URI.")

    return _client[DB_NAME][COLLECTION]


def init_db():
    """Create indexes for fast lookups (safe to run multiple times)."""
    col = get_collection()
    col.create_index("email_id", unique=True)
    col.create_index("label")
    col.create_index("urgency")
    col.create_index([("received", DESCENDING)])
    print("MongoDB indexes ready.")


def upsert_email(email: dict):
    """Insert or update a single email document."""
    col = get_collection()
    doc = {
        "email_id":     email.get("id"),
        "subject":      email.get("subject", ""),
        "preview":      email.get("preview", ""),
        "sender_email": email.get("from", ""),
        "sender_name":  email.get("sender_name", ""),
        "received":     email.get("received", ""),
        "folder":       email.get("folder", ""),
        "is_read":      email.get("is_read", False),
        "label":        email.get("label", "Awaiting Response"),
        "company":      email.get("company", "Unknown"),
        "job_title":    email.get("job_title", "Unknown"),
        "urgency":      email.get("urgency", "Low"),
        "summary":      email.get("summary", ""),
        "action_needed":email.get("action_needed", "None"),
        "confidence":   email.get("confidence", 0.0),
        "updated_at":   datetime.now(datetime.timezone.utc),
    }

    col.update_one(
        {"email_id": doc["email_id"]},
        {
            "$set": doc,
            "$setOnInsert": {"added_at": datetime.now(datetime.timezone.utc)}
        },
        upsert=True
    )


def save_emails(emails: list):
    """Bulk upsert a list of classified email dicts."""
    init_db()
    col = get_collection()

    operations = []
    for email in emails:
        doc = {
            "email_id":     email.get("id"),
            "subject":      email.get("subject", ""),
            "preview":      email.get("preview", ""),
            "sender_email": email.get("from", ""),
            "sender_name":  email.get("sender_name", ""),
            "received":     email.get("received", ""),
            "folder":       email.get("folder", ""),
            "is_read":      email.get("is_read", False),
            "label":        email.get("label", "Awaiting Response"),
            "company":      email.get("company", "Unknown"),
            "job_title":    email.get("job_title", "Unknown"),
            "urgency":      email.get("urgency", "Low"),
            "summary":      email.get("summary", ""),
            "action_needed":email.get("action_needed", "None"),
            "confidence":   email.get("confidence", 0.0),
            "updated_at":   datetime.now(),
        }
        operations.append(
            UpdateOne(
                {"email_id": doc["email_id"]},
                {"$set": doc, "$setOnInsert": {"added_at": datetime.now()}},
                upsert=True
            )
        )

    if operations:
        result = col.bulk_write(operations)
        print(f"Saved to MongoDB: {result.upserted_count} new, {result.modified_count} updated.")


def get_all_applications() -> list:
    """Return all applications sorted by most recent first."""
    col = get_collection()
    docs = col.find({}, {"_id": 0}).sort("received", DESCENDING)
    return list(docs)


def get_stats() -> dict:
    """Return count per label."""
    col = get_collection()
    pipeline = [
        {"$group": {"_id": "$label", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}}
    ]
    return {row["_id"]: row["count"] for row in col.aggregate(pipeline)}


def get_high_urgency() -> list:
    """Return High urgency emails that still need action."""
    col = get_collection()
    docs = col.find(
        {
            "urgency": "High",
            "label": {"$nin": ["Rejection", "Application Confirmed"]}
        },
        {"_id": 0}
    ).sort("received", DESCENDING)
    return list(docs)


if __name__ == "__main__":
    stats = get_stats()
    print("Current stats:", stats)