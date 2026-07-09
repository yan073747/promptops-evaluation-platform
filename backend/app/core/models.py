from dataclasses import dataclass


@dataclass(frozen=True)
class PromptVersion:
    id: int
    template_id: int
    label: str
    content: str
    change_note: str


@dataclass(frozen=True)
class TestCase:
    id: int
    input_text: str
    expected_keywords: list[str]


@dataclass(frozen=True)
class ModelOutput:
    text: str
    latency_ms: int
    cost_usd: float
    token_estimate: int


@dataclass(frozen=True)
class EvaluationResult:
    score: float
    passed: bool
    reason: str


@dataclass(frozen=True)
class BatchRunItem:
    test_case: TestCase
    rendered_prompt: str
    output: ModelOutput
    evaluation: EvaluationResult
    output_id: int | None = None
    human_score: float | None = None
    human_note: str = ""


@dataclass(frozen=True)
class BatchRunSummary:
    total_cases: int
    items: list[BatchRunItem]
    average_score: float
    failure_count: int
    total_cost_usd: float
    average_latency_ms: float
