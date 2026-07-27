import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./tps360_dev.db")


def get_engine() -> Engine:
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    return create_engine(DATABASE_URL, connect_args=connect_args)


engine = get_engine()
