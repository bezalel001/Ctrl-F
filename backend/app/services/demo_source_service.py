from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.source import Source, SourceCreate
from app.models.user import UserProfile
from app.services.source_service import create_source


@dataclass(frozen=True)
class DemoSourceSeedResult:
    created: int
    skipped: int
    source_ids: list[int]


DEMO_SOURCE_ACTOR = UserProfile(
    id="u_admin",
    name="Admin Demo",
    email="admin@example.com",
    role="admin",
    department="IT",
    permissions=["chat:use", "sources:manage", "feedback:review", "audit:read"],
)

DEMO_SOURCES = [
    SourceCreate(
        title="Vacation Policy",
        description="Fictitious paid time off and vacation guidance for demo questions.",
        source_type="document",
        location="data/approved_sources/hr/vacation.md",
        owning_department="Human Resources",
        allowed_roles=["admin", "employee", "hr", "intern", "manager"],
        allowed_departments=[],
        approval_status="approved",
        version="2026.1",
    ),
    SourceCreate(
        title="HR Policy",
        description="Fictitious HR policy covering work hours, PTO, sick leave, remote work, and equipment.",
        source_type="document",
        location="data/approved_sources/hr/hr-policy.md",
        owning_department="Human Resources",
        allowed_roles=["admin", "employee", "hr", "intern", "manager"],
        allowed_departments=[],
        approval_status="approved",
        version="2026.1",
    ),
    SourceCreate(
        title="IT Support FAQ",
        description="Fictitious IT support FAQ covering passwords, software, VPN, devices, and incidents.",
        source_type="document",
        location="data/approved_sources/it/support-faq.md",
        owning_department="IT",
        allowed_roles=["admin", "employee", "hr", "intern", "manager"],
        allowed_departments=[],
        approval_status="approved",
        version="2026.1",
    ),
    SourceCreate(
        title="New Hire Onboarding Guide",
        description="Fictitious onboarding checklist and access guidance for new employees.",
        source_type="document",
        location="data/approved_sources/onboarding/new-hire-guide.md",
        owning_department="People Operations",
        allowed_roles=["admin", "employee", "hr", "intern", "manager"],
        allowed_departments=[],
        approval_status="approved",
        version="2026.1",
    ),
    SourceCreate(
        title="Engineering Handbook",
        description="Fictitious engineering workflow, review, testing, access, and incident guidance.",
        source_type="document",
        location="data/approved_sources/engineering/engineering-handbook.md",
        owning_department="Engineering",
        allowed_roles=["admin", "manager"],
        allowed_departments=["Engineering"],
        approval_status="approved",
        version="2026.1",
    ),
]


def seed_demo_sources(session: Session, actor: UserProfile = DEMO_SOURCE_ACTOR) -> DemoSourceSeedResult:
    created = 0
    skipped = 0
    source_ids: list[int] = []

    for source_in in DEMO_SOURCES:
        existing = _get_source_by_location(session, source_in.location)
        if existing is not None:
            skipped += 1
            if existing.id is not None:
                source_ids.append(existing.id)
            continue

        source = create_source(session, source_in, actor)
        created += 1
        if source.id is not None:
            source_ids.append(source.id)

    return DemoSourceSeedResult(created=created, skipped=skipped, source_ids=source_ids)


def _get_source_by_location(session: Session, location: str) -> Source | None:
    statement = select(Source).where(Source.location == location)
    return session.exec(statement).first()
