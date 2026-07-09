# PromptOps Platform Design

## Goal

Build a small PromptOps platform for portfolio demonstration. The platform helps users manage prompt templates, run prompts against test cases, score model outputs, review failure cases, compare prompt versions, and track cost and latency.

## Audience

The project is aimed at HR screeners and technical interviewers for Prompt Engineer, AI Product Engineer, AI Agent Optimization, and junior AI application developer roles.

## MVP Scope

The first version must support this flow:

```text
Create prompt template
-> Create prompt version
-> Add test cases
-> Run batch evaluation in mock mode
-> Save outputs and automatic scores
-> Mark low-score outputs as failure cases
-> Compare two prompt versions
-> Show cost and latency metrics
```

## Product Pages

- Dashboard: total runs, average score, failure rate, total cost, average latency.
- Prompt Templates: create and view prompt templates and versions.
- Test Cases: create and view test questions and expected keywords.
- Batch Runs: run a prompt version against selected test cases.
- Results: inspect model outputs, automatic scores, human scores, and reasons.
- Failure Cases: review low-score cases and failure reasons.
- Version Comparison: compare score, pass rate, cost, and latency across prompt versions.

## Core Data Model

- `prompt_templates`: prompt name, task type, description.
- `prompt_versions`: prompt template content, version label, change note.
- `test_cases`: user input, expected keywords, expected intent, difficulty.
- `test_runs`: run name, provider mode, started time, total cost, average score.
- `model_outputs`: rendered prompt, model output text, latency, token estimate, cost.
- `evaluations`: automatic score, pass flag, score reason, human score, human note.
- `failure_cases`: failure type, severity, analysis note.
- `prompt_optimizations`: before version, after version, optimization note.

## Mock Mode

Mock mode returns deterministic outputs based on test case content. This makes the project easy to run without API keys and makes tests stable.

## Automatic Scoring

The first scoring rule is keyword-based:

- A test case defines expected keywords.
- The output is scored by keyword hit ratio.
- A case passes when the score is at least 0.7.
- A case below 0.7 becomes a failure case.

This is simple enough for a beginner and clear enough for interviews. Later versions can add LLM-as-judge scoring.

## Architecture

```text
frontend
  -> FastAPI routes
    -> application services
      -> SQLite repository
      -> mock model provider
      -> scoring service
```

The first day focuses on application services because they are easy to test and become the foundation for API routes and UI.

## Delivery Materials

- GitHub README
- Architecture documentation
- Screenshots
- Demo video script
- Resume project description
- Interview explanation notes

