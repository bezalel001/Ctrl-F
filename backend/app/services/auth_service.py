import base64
import hashlib
import hmac
import json
import random
from dataclasses import dataclass
from typing import Any

from app.models.user import UserProfile


class AuthenticationError(Exception):
    """Raised when credentials or access tokens are invalid."""


@dataclass(frozen=True)
class DemoUser:
    profile: UserProfile
    password: str


DEMO_USER_NAME_POOLS: dict[str, tuple[str, ...]] = {
    "employee": (
        "Maya Schneider",
        "Jonas Bauer",
        "Elena Fischer",
        "Tobias Weber",
    ),
    "intern": (
        "Lena Hoffmann",
        "Noah Wagner",
        "Sofia Becker",
        "Felix Gruber",
    ),
    "manager": (
        "Clara Meier",
        "Matthias Keller",
        "Nina Schwarz",
        "David Leitner",
    ),
    "hr": (
        "Anna Huber",
        "Markus Steiner",
        "Laura Wagner",
        "Simon Berger",
    ),
    "admin": (
        "Julia Richter",
        "Thomas Klein",
        "Marie Fuchs",
        "Patrick Hofer",
    ),
}


def _random_demo_name(role: str) -> str:
    return random.choice(DEMO_USER_NAME_POOLS[role])


DEMO_USERS: dict[str, DemoUser] = {
    "employee@example.com": DemoUser(
        profile=UserProfile(
            id="u_employee",
            name=_random_demo_name("employee"),
            email="employee@example.com",
            role="employee",
            department="People Operations",
            permissions=["chat:use"],
        ),
        password="demo",
    ),
    "intern@example.com": DemoUser(
        profile=UserProfile(
            id="u_intern",
            name=_random_demo_name("intern"),
            email="intern@example.com",
            role="intern",
            department="Engineering",
            permissions=["chat:use"],
        ),
        password="demo",
    ),
    "manager@example.com": DemoUser(
        profile=UserProfile(
            id="u_manager",
            name=_random_demo_name("manager"),
            email="manager@example.com",
            role="manager",
            department="Engineering",
            permissions=["chat:use", "feedback:review"],
        ),
        password="demo",
    ),
    "hr@example.com": DemoUser(
        profile=UserProfile(
            id="u_hr",
            name=_random_demo_name("hr"),
            email="hr@example.com",
            role="hr",
            department="Human Resources",
            permissions=["chat:use", "feedback:review"],
        ),
        password="demo",
    ),
    "admin@example.com": DemoUser(
        profile=UserProfile(
            id="u_admin",
            name=_random_demo_name("admin"),
            email="admin@example.com",
            role="admin",
            department="IT",
            permissions=["chat:use", "sources:manage", "feedback:review", "audit:read"],
        ),
        password="demo",
    ),
}


def authenticate_user(email: str, password: str) -> UserProfile:
    demo_user = DEMO_USERS.get(email.lower())
    if demo_user is None or not hmac.compare_digest(demo_user.password, password):
        raise AuthenticationError("Invalid credentials")

    return demo_user.profile


def get_user_by_id(user_id: str) -> UserProfile | None:
    for demo_user in DEMO_USERS.values():
        if demo_user.profile.id == user_id:
            return demo_user.profile

    return None


def create_access_token(user: UserProfile, secret: str) -> str:
    payload = {"sub": user.id, "email": user.email}
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(encoded_payload, secret)
    return f"{encoded_payload}.{signature}"


def resolve_user_from_token(token: str, secret: str) -> UserProfile:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise AuthenticationError("Invalid token format") from exc

    expected_signature = _sign(encoded_payload, secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthenticationError("Invalid token signature")

    payload = _decode_payload(encoded_payload)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise AuthenticationError("Token subject missing")

    user = get_user_by_id(user_id)
    if user is None:
        raise AuthenticationError("User not found")

    return user


def _decode_payload(encoded_payload: str) -> dict[str, Any]:
    try:
        decoded = base64.urlsafe_b64decode(_pad_base64(encoded_payload)).decode("utf-8")
        payload = json.loads(decoded)
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid token payload") from exc

    if not isinstance(payload, dict):
        raise AuthenticationError("Invalid token payload")

    return payload


def _sign(encoded_payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _pad_base64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return f"{value}{padding}".encode("utf-8")
