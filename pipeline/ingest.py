# ingest.py

import json
import os
from constants.service import UPLOADS_PATH, UPLOADS_TEST_PATH
import re
import time
from config import logger
import os
import glob

from streaming_history_analyser.process import exploit_streaming_history, IngestContext

FILENAME_RE = re.compile(
    r"^Streaming_History_Audio_(?:\d{4}(?:-\d{4})*)_\d{1,2}\.json$"
)


def delete_log_backup():
    # We delete all the backup log files to restart to zero
    for filepath in glob.glob("./log/exploit_streaming_history.log*"):
        if os.path.basename(filepath) == "exploit_streaming_history.log":
            pass
        else:
            os.remove(filepath)


def list_upload_filenames() -> list[str]:
    """Return the sorted list of valid streaming history filenames in UPLOADS_PATH."""
    try:
        all_files = os.listdir(UPLOADS_PATH)
    except Exception as e:
        raise e

    valid = []
    for filename in all_files:
        if not FILENAME_RE.search(filename):
            raise ValueError(
                f"The file name {filename} is not correct, you should not rename the files sent by Spotify."
            )
        valid.append(filename)

    pattern = re.compile(r"(\d{1,2})(?=\.json$)")
    return sorted(valid, key=lambda fn: int(pattern.search(fn).group(1)))


def load_streaming_history_folder(user_id: str):
    delete_log_backup()
    filenames = list_upload_filenames()
    ctx = IngestContext(user_id=user_id)

    for filename in filenames:
        streaming_history = load_streaming_history_file(filename)
        exploit_streaming_history(streaming_history, ctx)
        logger.info(f"ALGORITHM DONE FOR FILENAME {filename}")


def load_streaming_history_selected(
    user_id: str, filenames: list[str]
) -> dict[str, dict[str, float]]:
    """Process only the given filenames (must be in sorted order for streak continuity).
    Returns a dict {filename: timings} for display in the UI.
    """
    ctx = IngestContext(user_id=user_id)
    all_timings: dict[str, dict[str, float]] = {}

    for filename in filenames:
        t_file_start = time.perf_counter()
        streaming_history = load_streaming_history_file(filename)
        timings = exploit_streaming_history(streaming_history, ctx)
        timings["total_file"] = time.perf_counter() - t_file_start
        all_timings[filename] = timings
        logger.info(f"ALGORITHM DONE FOR FILENAME {filename}")

    return all_timings


def load_streaming_history_file(filename: str):
    path = UPLOADS_PATH + filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise e
