"""
Runs sync every 6 hours automatically inside Docker.
Logs each run with timestamp. Runs once immediately on startup.
"""

import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

SYNC_INTERVAL_HOURS = 6
SYNC_INTERVAL_SECS  = SYNC_INTERVAL_HOURS * 60 * 60


def run():
    from sync import run_sync

    logging.info("=" * 45)
    logging.info("Job Tracker Scheduler started.")
    logging.info(f"Syncing every {SYNC_INTERVAL_HOURS} hours.")
    logging.info("=" * 45)

    while True:
        logging.info(f"▶ Starting sync at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        try:
            run_sync()
            logging.info("Sync completed successfully.")
        except Exception as e:
            logging.error(f"Sync failed: {e}")

        logging.info(f"Next sync in {SYNC_INTERVAL_HOURS} hours.")
        time.sleep(SYNC_INTERVAL_SECS)


if __name__ == "__main__":
    run()