import argparse
from pathlib import Path

from app.evaluation.runner import DEFAULT_CASES_PATH, load_cases, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ctrl-F demo RAG evaluation cases.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running backend base URL.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH, help="Evaluation cases JSON file.")
    parser.add_argument("--password", default="demo", help="Demo user password.")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    results = run_evaluation(base_url=args.base_url, cases=cases, password=args.password)
    failures = [result for result in results if not result.passed]

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        sources = ", ".join(result.source_titles) if result.source_titles else "none"
        print(
            f"{status} {result.case_id} turn {result.turn_index} "
            f"({result.elapsed_seconds:.2f}s, confidence {result.confidence:.2f}, sources: {sources})"
        )
        for failure in result.failures:
            print(f"  - {failure}")

    print(f"\n{len(results) - len(failures)}/{len(results)} turns passed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
