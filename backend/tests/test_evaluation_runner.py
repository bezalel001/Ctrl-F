from pathlib import Path

from app.evaluation.runner import EvaluationTurn, evaluate_turn, load_cases


def test_load_demo_evaluation_cases() -> None:
    cases = load_cases(Path("../data/evaluation/demo_cases.json"))

    assert {case.id for case in cases} >= {
        "hr-pto-direct",
        "it-lost-laptop",
        "onboarding-followup",
        "restricted-engineering-employee",
        "outside-scope",
    }
    assert all(case.turns for case in cases)


def test_evaluate_turn_passes_expected_source_and_terms() -> None:
    result = evaluate_turn(
        case_id="hr-pto-direct",
        turn_index=1,
        turn=EvaluationTurn(
            question="How many paid vacation days?",
            expected_source_titles=["HR Policy"],
            expected_answer_terms=["25", "vacation"],
        ),
        response={
            "answer": "Employees receive 25 paid vacation days.",
            "sources": [{"title": "HR Policy"}],
            "confidence": 0.91,
            "warning": None,
        },
        elapsed_seconds=0.25,
    )

    assert result.passed is True
    assert result.failures == []


def test_evaluate_turn_fails_for_forbidden_source() -> None:
    result = evaluate_turn(
        case_id="restricted-engineering-employee",
        turn_index=1,
        turn=EvaluationTurn(
            question="What are the production database rules?",
            expect_fallback=True,
            expect_warning=True,
            forbidden_source_titles=["Engineering Handbook"],
        ),
        response={
            "answer": "Production database access is read-only by default.",
            "sources": [{"title": "Engineering Handbook"}],
            "confidence": 0.92,
            "warning": None,
        },
        elapsed_seconds=0.25,
    )

    assert result.passed is False
    assert "forbidden source returned: Engineering Handbook" in result.failures
    assert "expected fallback without sources" in result.failures
    assert "expected confidence warning" in result.failures


def test_evaluate_turn_passes_safe_fallback() -> None:
    result = evaluate_turn(
        case_id="outside-scope",
        turn_index=1,
        turn=EvaluationTurn(
            question="What is the cafeteria menu?",
            expect_fallback=True,
            expect_warning=True,
        ),
        response={
            "answer": "I don't know based on the approved company sources available to me.",
            "sources": [],
            "confidence": 0.0,
            "warning": "Confidence is below 85%; verify with a human owner before acting on this answer.",
        },
        elapsed_seconds=0.25,
    )

    assert result.passed is True
