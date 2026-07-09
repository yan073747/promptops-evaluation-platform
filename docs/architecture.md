# PromptOps Architecture

## Simple Explanation

PromptOps treats prompts like software. A prompt version is tested against many cases, each model output is scored, and low-score outputs become failure cases for later optimization.

## System Flow

```text
User
-> Frontend dashboard
-> FastAPI routes
-> Batch runner
-> Prompt renderer
-> Mock model provider
-> Evaluator
-> SQLite repository
```

## Backend Modules

- `backend/app/core/models.py`: shared data objects.
- `backend/app/services/prompt_renderer.py`: replaces variables such as `{{user_input}}`.
- `backend/app/services/mock_model.py`: returns deterministic mock outputs without API keys.
- `backend/app/services/evaluator.py`: scores outputs using expected keyword hit ratio.
- `backend/app/services/batch_runner.py`: runs prompt versions against test cases and returns metrics.
- `backend/app/db/repository.py`: saves prompt data, test cases, runs, outputs, scores, and failures in SQLite.
- `backend/app/main.py`: exposes FastAPI endpoints for dashboard data and mock batch runs.

## Why Mock Mode Comes First

Mock mode makes the project stable for local demos, screenshots, and tests. Real model providers can be added after the workflow is proven.

## API Layer

The API currently exposes:

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/prompt-versions`
- `POST /api/prompt-versions`
- `PUT /api/prompt-versions/{version_id}`
- `GET /api/test-cases`
- `POST /api/test-cases`
- `PUT /api/test-cases/{case_id}`
- `GET /api/failure-cases`
- `POST /api/runs/mock`
- `PUT /api/model-outputs/{output_id}/human-review`
- `GET /api/prompt-version-comparison`
- `POST /api/demo/reset`

The frontend can call these endpoints to turn the static shell into an interactive app.

## Frontend Integration

FastAPI serves the frontend at `/` and static files under `/static`. The dashboard calls:

- `/api/dashboard` on page load.
- `/api/prompt-versions` on page load and after saving a prompt version.
- `/api/test-cases` on page load and after saving a test case.
- `/api/failure-cases` on page load and after a batch run.
- `/api/runs/mock` when the user clicks `Run Mock Batch`.
- `/api/model-outputs/{output_id}/human-review` when the user saves manual review.
- `/api/prompt-version-comparison` on page load and after every batch run.
- `/api/demo/reset` when the user resets demo data.

This keeps the beginner setup simple: one backend server runs both the API and the frontend.

The current frontend supports creating and editing prompt versions and test cases. Batch runs use the selected prompt version from the dropdown. Each output row also supports a human score and review note, which are saved back to SQLite.

The version comparison section is computed from real `test_runs` history. For each prompt version, the platform shows run count, total tested cases, average score, failure rate, total cost, and average latency.

## Failure Analysis

Failure cases are generated when automatic scoring does not pass. The system stores:

- failed test case id
- model output id
- failure type
- severity
- score reason
- optimization suggestion

The frontend displays these as analysis cards so reviewers can see what failed, why it failed, and how to improve the prompt.

## Demo Reset Flow

The reset action clears runtime tables and restores seed data. It is meant for repeatable technical demos, local verification, and screen recordings.

Reset clears:

- prompt versions and prompt templates
- test cases
- test runs
- model outputs
- failure cases

Then it seeds the default prompt template, default `v1` prompt version, and three default test cases.

## Database Tables

- `prompt_templates`
- `prompt_versions`
- `test_cases`
- `test_runs`
- `model_outputs`
- `failure_cases`

`model_outputs` stores both automatic evaluation data and manual review data:

- `score`: automatic keyword score.
- `score_reason`: automatic scoring explanation.
- `human_score`: manual reviewer score.
- `human_note`: manual reviewer note.
