from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


def create_database_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = create_database_engine(get_settings().database_url)


def init_db() -> None:
    # Import table models before metadata creation.
    from app.models import conversation as _conversation  # noqa: F401
    from app.models import feedback as _feedback  # noqa: F401
    from app.models import source as _source  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
