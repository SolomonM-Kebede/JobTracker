"""
Main sync script: fetch → classify → save
Run this manually or schedule it with cron.
"""

from fetch_emails import fetch_all_job_emails
from classify import classify_batch
from database import save_emails, get_stats


def run_sync(max_per_folder: int = 50):
    print("=" * 50)
    print("Job Tracker Sync Starting...")
    print("=" * 50)

    # Step 1: Fetch emails from all folders
    emails = fetch_all_job_emails(max_per_folder=max_per_folder)

    if not emails:
        print("\n No new job-related emails found.")
        return

    # Step 2: Classify with Claude
    print(f"\n Classifying {len(emails)} emails with Claude...")
    classified = classify_batch(emails)

    # Step 3: Save to database
    print(f"\n Saving to database...")
    save_emails(classified)

    # Print summary
    stats = get_stats()
    print("\n" + "=" * 50)
    print(" SYNC COMPLETE — Current Breakdown:")
    print("=" * 50)
    for label, count in stats.items():
        emoji = {
            "Rejection":            "❌",
            "Interview Invite":     "🎯",
            "Job Offer":            "🎉",
            "Assessment/Task":      "📝",
            "Follow-up Needed":     "⚡",
            "Application Confirmed":"✅",
            "Awaiting Response":    "⏳",
        }.get(label, "📧")
        print(f"  {emoji}  {label:<25} {count}")
    print("=" * 50)
    print("\n Run `streamlit run dashboard.py` to view your tracker!")


if __name__ == "__main__":
    run_sync()