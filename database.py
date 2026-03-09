"""
MongoDB Atlas storage with paginated/filtered queries.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne, DESCENDING
from pymongo.errors import ConnectionFailure

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME     = "job_tracker"
COLLECTION  = "applications"

_client = None


def get_collection():
    global _client
    if _client is None:
        if not MONGODB_URI:
            raise ValueError("MONGODB_URI not set in .env")
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        try:
            _client.admin.command("ping")
        except ConnectionFailure:
            raise ConnectionFailure("Could not connect to MongoDB Atlas.")
    return _client[DB_NAME][COLLECTION]


def init_db():
    col = get_collection()
    col.create_index("email_id", unique=True)
    col.create_index("label")
    col.create_index("urgency")
    col.create_index("company")
    col.create_index("department")
    col.create_index([("received", DESCENDING)])


def save_emails(emails: list):
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
            "urgency":      email.get("urgency", "Low"),
            "summary":      email.get("summary", ""),
            "action_needed":email.get("action_needed", "None"),
            "confidence":   email.get("confidence", 0.0),
            "company":      email.get("company", "Unknown"),
            "job_title":    email.get("job_title", "Unknown"),
            "department":   email.get("department", "Unknown"),
            "documents":    email.get("documents", "Not specified"),
            "sent_date":    email.get("sent_date", ""),
            "deadline":     email.get("deadline", ""),
            "ad_link":      email.get("ad_link", ""),
            "updated_at":   datetime.utcnow(),
        }
        operations.append(
            UpdateOne(
                {"email_id": doc["email_id"]},
                {
                    "$set": {k: v for k, v in doc.items() if k != "notes"},
                    "$setOnInsert": {"added_at": datetime.utcnow(), "notes": ""}
                },
                upsert=True
            )
        )
    if operations:
        result = col.bulk_write(operations)
        print(f"💾 Saved: {result.upserted_count} new, {result.modified_count} updated.")


def get_stats() -> dict:
    """Returns label counts — lightweight, always loaded."""
    col = get_collection()
    pipeline = [
        {"$group": {"_id": "$label", "count": {"$sum": 1}}},
        {"$sort": {"count": DESCENDING}}
    ]
    return {row["_id"]: row["count"] for row in col.aggregate(pipeline)}


def get_applications_by_label(label: str, page: int = 0,
                               page_size: int = 10, search: str = "",
                               department: str = "") -> list:
    """
    Fetch only the applications for a specific label — paginated.
    Optionally filter by search term and department.
    """
    col = get_collection()
    query = {}

    if label != "All":
        query["label"] = label

    if department and department != "All Departments":
        query["department"] = department

    if search:
        query["$or"] = [
            {"company":   {"$regex": search, "$options": "i"}},
            {"job_title": {"$regex": search, "$options": "i"}},
            {"subject":   {"$regex": search, "$options": "i"}},
        ]

    return list(
        col.find(query, {"_id": 0})
           .sort("received", DESCENDING)
           .skip(page * page_size)
           .limit(page_size)
    )


def get_total_count(label: str = "All", search: str = "",
                    department: str = "") -> int:
    """Count matching documents for pagination."""
    col = get_collection()
    query = {}
    if label != "All":
        query["label"] = label
    if department and department != "All Departments":
        query["department"] = department
    if search:
        query["$or"] = [
            {"company":   {"$regex": search, "$options": "i"}},
            {"job_title": {"$regex": search, "$options": "i"}},
            {"subject":   {"$regex": search, "$options": "i"}},
        ]
    return col.count_documents(query)


def get_departments() -> list:
    """Get distinct department values for filter dropdown."""
    col = get_collection()
    return sorted([d for d in col.distinct("department") if d and d != "Unknown"])


def get_high_urgency() -> list:
    col = get_collection()
    return list(col.find(
        {"urgency": "High", "label": {"$nin": ["Rejection", "Application Confirmed"]}},
        {"_id": 0}
    ).sort("received", DESCENDING).limit(5))


def update_fields(email_id: str, fields: dict):
    col = get_collection()
    col.update_one({"email_id": email_id}, {"$set": fields})


if __name__ == "__main__":
    print("Stats:", get_stats())