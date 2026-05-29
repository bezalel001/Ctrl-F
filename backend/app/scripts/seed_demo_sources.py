from sqlmodel import Session

from app.services.demo_source_service import seed_demo_sources
from app.storage.database import engine, init_db


def main() -> None:
    init_db()
    with Session(engine) as session:
        result = seed_demo_sources(session)

    print(
        "Demo sources registered: "
        f"{result.created} created, {result.skipped} skipped, {len(result.source_ids)} total"
    )


if __name__ == "__main__":
    main()
