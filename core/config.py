import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.orm.base import Base
import logging
from logging.handlers import RotatingFileHandler
from typing import Final

load_dotenv()

uid = os.getenv("UID")
pwd = os.getenv("PASSWORD")
server = os.getenv("SERVER")
port = os.getenv("PORT")
databse = os.getenv("DATABASE")

engine = create_engine(f"postgresql://{uid}:{pwd}@{server}:{port}/{databse}")
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

session = Session()

# Logger config variables
MAX_BYTES_PER_FILE: Final[int] = 3_800_000
LOG_FILE_NAME: Final[str] = "exploit_streaming_history"
BACKUP_COUNT: Final[int] = 10
LOG_FORMAT: Final[str] = "%(asctime)s.%(msecs)03d %(message)s"
DATE_FORMAT: Final[str] = "%H:%M:%S"

# Logger setup
os.makedirs("./log", exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    f"./log/{LOG_FILE_NAME}.log",
    mode="w",
    maxBytes=MAX_BYTES_PER_FILE,
    encoding="utf-8",
    backupCount=BACKUP_COUNT,
)
handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

logger.addHandler(handler)
