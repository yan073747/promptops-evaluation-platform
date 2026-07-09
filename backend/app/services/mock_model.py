from backend.app.core.models import ModelOutput, TestCase


def generate_mock_output(test_case: TestCase) -> ModelOutput:
    if "故意失败" in test_case.input_text:
        text = "Mock 回答：请联系人工客服处理。"
        token_estimate = max(1, len(text.split()))
        return ModelOutput(
            text=text,
            latency_ms=120 + test_case.id,
            cost_usd=round(token_estimate * 0.00001, 6),
            token_estimate=token_estimate,
        )

    keyword_text = ", ".join(test_case.expected_keywords)
    text = (
        f"Mock 回答：{test_case.input_text}。"
        f"回答应覆盖这些要点：{keyword_text}。"
    )
    token_estimate = max(1, len(text.split()))
    return ModelOutput(
        text=text,
        latency_ms=120 + test_case.id,
        cost_usd=round(token_estimate * 0.00001, 6),
        token_estimate=token_estimate,
    )
