from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

DEFAULT_CASES_PATH = Path(__file__).resolve().parents[3] / "data" / "evaluation" / "demo_cases.json"
FALLBACK_ANSWER_PREFIX = "I don't know based on the approved company sources"


@dataclass(frozen=True)
class EvaluationTurn:
    question: str
    expected_source_titles: list[str] = field(default_factory=list)
    expected_answer_terms: list[str] = field(default_factory=list)
    forbidden_source_titles: list[str] = field(default_factory=list)
    expect_fallback: bool = False
    expect_warning: bool = False
    max_seconds: float = 5.0


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    name: str
    user_email: str
    turns: list[EvaluationTurn]


@dataclass(frozen=True)
class EvaluationTurnResult:
    case_id: str
    turn_index: int
    question: str
    passed: bool
    elapsed_seconds: float
    failures: list[str]
    source_titles: list[str]
    confidence: float
    warning: str | None


def load_cases(path: Path = DEFAULT_CASES_PATH) -> list[EvaluationCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [_case_from_payload(item) for item in payload["cases"]]


def evaluate_turn(
    *,
    case_id: str,
    turn_index: int,
    turn: EvaluationTurn,
    response: dict[str, Any],
    elapsed_seconds: float,
) -> EvaluationTurnResult:
    source_titles = [str(source.get("title")) for source in response.get("sources", [])]
    answer = str(response.get("answer", ""))
    answer_lower = answer.lower()
    warning = response.get("warning")
    confidence = float(response.get("confidence", 0.0))
    failures: list[str] = []

    if elapsed_seconds > turn.max_seconds:
        failures.append(f"response took {elapsed_seconds:.2f}s, expected <= {turn.max_seconds:.2f}s")

    for title in turn.expected_source_titles:
        if title not in source_titles:
            failures.append(f"missing expected source: {title}")

    for title in turn.forbidden_source_titles:
        if title in source_titles:
            failures.append(f"forbidden source returned: {title}")

    for term in turn.expected_answer_terms:
        if term.lower() not in answer_lower:
            failures.append(f"missing expected answer term: {term}")

    if turn.expect_fallback:
        if response.get("sources"):
            failures.append("expected fallback without sources")
        if FALLBACK_ANSWER_PREFIX.lower() not in answer_lower:
            failures.append("expected safe fallback answer")

    if turn.expect_warning and not warning:
        failures.append("expected confidence warning")

    return EvaluationTurnResult(
        case_id=case_id,
        turn_index=turn_index,
        question=turn.question,
        passed=not failures,
        elapsed_seconds=elapsed_seconds,
        failures=failures,
        source_titles=source_titles,
        confidence=confidence,
        warning=str(warning) if warning else None,
    )


def run_evaluation(
    *,
    base_url: str,
    cases: list[EvaluationCase],
    password: str = "demo",
    timeout_seconds: float = 60.0,
) -> list[EvaluationTurnResult]:
    tokens: dict[str, str] = {}
    results: list[EvaluationTurnResult] = []

    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds) as client:
        for case in cases:
            token = tokens.get(case.user_email)
            if token is None:
                token = _login(client, case.user_email, password)
                tokens[case.user_email] = token

            conversation_id: str | None = None
            for turn_index, turn in enumerate(case.turns, start=1):
                started_at = time.perf_counter()
                response = client.post(
                    "/api/chat",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"question": turn.question, "conversation_id": conversation_id},
                )
                elapsed_seconds = time.perf_counter() - started_at
                response.raise_for_status()
                payload = response.json()
                conversation_id = payload["conversation_id"]
                results.append(
                    evaluate_turn(
                        case_id=case.id,
                        turn_index=turn_index,
                        turn=turn,
                        response=payload,
                        elapsed_seconds=elapsed_seconds,
                    )
                )

    return results


def _login(client: httpx.Client, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    response.raise_for_status()
    return str(response.json()["access_token"])


def _case_from_payload(payload: dict[str, Any]) -> EvaluationCase:
    return EvaluationCase(
        id=str(payload["id"]),
        name=str(payload["name"]),
        user_email=str(payload["user_email"]),
        turns=[_turn_from_payload(item) for item in payload["turns"]],
    )


def _turn_from_payload(payload: dict[str, Any]) -> EvaluationTurn:
    return EvaluationTurn(
        question=str(payload["question"]),
        expected_source_titles=[str(item) for item in payload.get("expected_source_titles", [])],
        expected_answer_terms=[str(item) for item in payload.get("expected_answer_terms", [])],
        forbidden_source_titles=[str(item) for item in payload.get("forbidden_source_titles", [])],
        expect_fallback=bool(payload.get("expect_fallback", False)),
        expect_warning=bool(payload.get("expect_warning", False)),
        max_seconds=float(payload.get("max_seconds", 5.0)),
    )
