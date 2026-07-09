from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.app.db.repository import PromptOpsRepository


class MockRunRequest(BaseModel):
    prompt_version_id: int = 1


class PromptVersionCreate(BaseModel):
    template_id: int = 1
    label: str
    content: str
    change_note: str


class PromptVersionUpdate(BaseModel):
    label: str
    content: str
    change_note: str


class TestCaseWrite(BaseModel):
    input_text: str
    expected_keywords: list[str]


class HumanReviewWrite(BaseModel):
    human_score: float
    human_note: str


def create_app(db_path: str | Path = "backend/data/promptops.db") -> FastAPI:
    app = FastAPI(title="PromptOps Evaluation Platform")
    repository = PromptOpsRepository(db_path)
    repository.initialize()
    repository.seed_demo_data()
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def frontend() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/dashboard")
    def dashboard() -> dict[str, int | float]:
        return repository.get_dashboard_metrics()

    @app.post("/api/demo/reset")
    def reset_demo_data() -> dict[str, str]:
        repository.reset_demo_data()
        return {"status": "reset"}

    @app.get("/api/prompt-versions")
    def prompt_versions() -> list[dict[str, object]]:
        return [
            {
                "id": item.id,
                "template_id": item.template_id,
                "label": item.label,
                "content": item.content,
                "change_note": item.change_note,
            }
            for item in repository.list_prompt_versions()
        ]

    @app.post("/api/prompt-versions")
    def create_prompt_version(payload: PromptVersionCreate) -> dict[str, object]:
        item = repository.create_prompt_version(
            template_id=payload.template_id,
            label=payload.label,
            content=payload.content,
            change_note=payload.change_note,
        )
        return {
            "id": item.id,
            "template_id": item.template_id,
            "label": item.label,
            "content": item.content,
            "change_note": item.change_note,
        }

    @app.put("/api/prompt-versions/{version_id}")
    def update_prompt_version(
        version_id: int,
        payload: PromptVersionUpdate,
    ) -> dict[str, object]:
        try:
            item = repository.update_prompt_version(
                version_id=version_id,
                label=payload.label,
                content=payload.content,
                change_note=payload.change_note,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {
            "id": item.id,
            "template_id": item.template_id,
            "label": item.label,
            "content": item.content,
            "change_note": item.change_note,
        }

    @app.get("/api/test-cases")
    def test_cases() -> list[dict[str, object]]:
        return [
            {
                "id": item.id,
                "input_text": item.input_text,
                "expected_keywords": item.expected_keywords,
            }
            for item in repository.list_test_cases()
        ]

    @app.post("/api/test-cases")
    def create_test_case(payload: TestCaseWrite) -> dict[str, object]:
        item = repository.create_test_case(
            input_text=payload.input_text,
            expected_keywords=payload.expected_keywords,
        )
        return {
            "id": item.id,
            "input_text": item.input_text,
            "expected_keywords": item.expected_keywords,
        }

    @app.put("/api/test-cases/{case_id}")
    def update_test_case(case_id: int, payload: TestCaseWrite) -> dict[str, object]:
        try:
            item = repository.update_test_case(
                case_id=case_id,
                input_text=payload.input_text,
                expected_keywords=payload.expected_keywords,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return {
            "id": item.id,
            "input_text": item.input_text,
            "expected_keywords": item.expected_keywords,
        }

    @app.get("/api/failure-cases")
    def failure_cases() -> list[dict[str, object]]:
        return repository.list_failure_cases()

    @app.get("/api/prompt-version-comparison")
    def prompt_version_comparison() -> list[dict[str, object]]:
        return repository.get_prompt_version_comparison()

    @app.put("/api/model-outputs/{output_id}/human-review")
    def update_human_review(
        output_id: int,
        payload: HumanReviewWrite,
    ) -> dict[str, object]:
        try:
            return repository.update_human_review(
                output_id=output_id,
                human_score=payload.human_score,
                human_note=payload.human_note,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/runs/mock")
    def run_mock_batch(request: MockRunRequest) -> dict[str, object]:
        try:
            version = repository.get_prompt_version(request.prompt_version_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        summary = repository.create_batch_run(version, repository.list_test_cases())
        return {
            "total_cases": summary.total_cases,
            "average_score": summary.average_score,
            "failure_count": summary.failure_count,
            "total_cost_usd": summary.total_cost_usd,
            "average_latency_ms": summary.average_latency_ms,
            "items": [
                {
                    "output_id": item.output_id,
                    "test_case_id": item.test_case.id,
                    "input_text": item.test_case.input_text,
                    "rendered_prompt": item.rendered_prompt,
                    "output_text": item.output.text,
                    "score": item.evaluation.score,
                    "passed": item.evaluation.passed,
                    "reason": item.evaluation.reason,
                    "human_score": item.human_score,
                    "human_note": item.human_note,
                    "latency_ms": item.output.latency_ms,
                    "cost_usd": item.output.cost_usd,
                }
                for item in summary.items
            ],
        }

    return app


app = create_app()
