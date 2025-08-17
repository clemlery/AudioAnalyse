# ingest.py

import json
import os
from constants.service import UPLOADS_PATH, UPLOADS_TEST_PATH
import re
from config import logger
import os
import glob

from streaming_history_analyser.process import exploit_streaming_history


def delete_log_backup():
    # We delete all the logs file to restart to zero
    for filepath in glob.glob("./log/exploit_streaming_history.log*"):
        if filepath == "./log/exploit_streaming_history.log":
            pass
        else:
            os.remove(filepath)


def load_streaming_history_folder():
    delete_log_backup()
    
    try:
        filenames = os.listdir(UPLOADS_TEST_PATH)
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

    for filename in filenames:
        streaming_history = load_streaming_history_file(filename)
        exploit_streaming_history(streaming_history)
        logger.info(f"ALGORITHM DONE FOR FILENAME {filename}")


def load_streaming_history_file(filename: str):
    path = UPLOADS_TEST_PATH + filename
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise e
