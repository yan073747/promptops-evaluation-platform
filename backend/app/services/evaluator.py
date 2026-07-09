from backend.app.core.models import EvaluationResult, TestCase


PASS_THRESHOLD = 0.7


def score_output(output_text: str, test_case: TestCase) -> EvaluationResult:
    if not test_case.expected_keywords:
        return EvaluationResult(score=1.0, passed=True, reason="No expected keywords.")

    normalized_output = output_text.lower()
    hits = [
        keyword
        for keyword in test_case.expected_keywords
        if keyword.lower() in normalized_output
    ]
    score = round(len(hits) / len(test_case.expected_keywords), 2)
    return EvaluationResult(
        score=score,
        passed=score >= PASS_THRESHOLD,
        reason=f"Matched {len(hits)}/{len(test_case.expected_keywords)} expected keywords.",
    )

