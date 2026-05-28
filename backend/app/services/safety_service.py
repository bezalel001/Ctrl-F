from app.models.user import UserProfile
from app.services.retrieval_service import RetrievedChunk


def suggested_contacts(user: UserProfile, chunks: list[RetrievedChunk]) -> list[str]:
    departments = [chunk.owning_department for chunk in chunks if chunk.owning_department]
    if not departments:
        departments = [user.department]

    contacts = [_contact_for_department(department) for department in departments]
    contacts.append("IT Support")

    deduped: list[str] = []
    for contact in contacts:
        if contact not in deduped:
            deduped.append(contact)

    return deduped


def _contact_for_department(department: str) -> str:
    normalized = department.strip().lower()
    if normalized in {"human resources", "people operations", "hr"}:
        return "Human Resources"
    if normalized in {"it", "information technology"}:
        return "IT Support"

    return f"{department} Knowledge Owner"
