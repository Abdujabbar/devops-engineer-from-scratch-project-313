import os

from sqlmodel import SQLModel, create_engine, Session
from shortener.models import *  # noqa: F403

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./shortener.db")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
