from sqlmodel import Session, SQLModel, create_engine, select

from app.models.source import Source
from app.services.demo_source_service import DEMO_SOURCES, seed_demo_sources


def test_seed_demo_sources_creates_approved_sources_once() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        first_result = seed_demo_sources(session)
        second_result = seed_demo_sources(session)
        sources = list(session.exec(select(Source)).all())

    assert first_result.created == len(DEMO_SOURCES)
    assert first_result.skipped == 0
    assert second_result.created == 0
    assert second_result.skipped == len(DEMO_SOURCES)
    assert len(sources) == len(DEMO_SOURCES)
    assert {source.location for source in sources} == {source.location for source in DEMO_SOURCES}
    assert all(source.approval_status == "approved" for source in sources)
