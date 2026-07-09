from backend.app.core.models import BatchRunItem, BatchRunSummary, PromptVersion, TestCase
from backend.app.services.evaluator import score_output
from backend.app.services.mock_model import generate_mock_output
from backend.app.services.prompt_renderer import render_prompt


def run_batch(version: PromptVersion, test_cases: list[TestCase]) -> BatchRunSummary:
    items: list[BatchRunItem] = []
    for test_case in test_cases:
        rendered_prompt = render_prompt(version, test_case)
        output = generate_mock_output(test_case)
        evaluation = score_output(output.text, test_case)
        items.append(
            BatchRunItem(
                test_case=test_case,
                rendered_prompt=rendered_prompt,
                output=output,
                evaluation=evaluation,
            )
        )

    total_cases = len(items)
    total_score = sum(item.evaluation.score for item in items)
    total_cost = sum(item.output.cost_usd for item in items)
    total_latency = sum(item.output.latency_ms for item in items)
    failure_count = sum(1 for item in items if not item.evaluation.passed)

    return BatchRunSummary(
        total_cases=total_cases,
        items=items,
        average_score=round(total_score / total_cases, 2) if total_cases else 0,
        failure_count=failure_count,
        total_cost_usd=round(total_cost, 6),
        average_latency_ms=round(total_latency / total_cases, 2) if total_cases else 0,
    )
