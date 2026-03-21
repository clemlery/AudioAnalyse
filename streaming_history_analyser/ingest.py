# ingest.py

import json
import os
from constants.service import UPLOADS_PATH, UPLOADS_TEST_PATH
import re
from config import logger
import os
import glob

from streaming_history_analyser.process import exploit_streaming_history, IngestContext


def delete_log_backup():
    # We delete all the backup log files to restart to zero
    for filepath in glob.glob("./log/exploit_streaming_history.log*"):
        if os.path.basename(filepath) == "exploit_streaming_history.log":
            pass
        else:
            os.remove(filepath)


def load_streaming_history_folder(user_id: str):
    delete_log_backup()

    try:
        filenames = os.listdir(UPLOADS_PATH)
    except Exception as e:
        raise e

    for filename in filenames:
        if not re.search(
            r"^Streaming_History_Audio_(?:\d{4}(?:-\d{4})*)_\d{1,2}\.json$", filename
        ):
            raise ValueError(
                f"The file name {filename} is not correct, you should not rename the files sent by Spotify."
            )

    pattern = re.compile(r"(\d{1,2})(?=\.json$)")
    filenames = sorted(filenames, key=lambda fn: int(pattern.search(fn).group(1)))

    # One context per user — streaks persist across files from the same export
    ctx = IngestContext(user_id=user_id)

    for filename in filenames:
        streaming_history = load_streaming_history_file(filename)
        exploit_streaming_history(streaming_history, ctx)
        logger.info(f"ALGORITHM DONE FOR FILENAME {filename}")


def load_streaming_history_file(filename: str):
    path = UPLOADS_PATH + filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise e
