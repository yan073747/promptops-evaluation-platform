# PromptOps MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first PromptOps skeleton with tested backend services, mock evaluation flow, and a simple frontend shell.

**Architecture:** The first implementation uses small Python service modules with dataclasses. FastAPI routes and a richer frontend can sit on top of these services without changing core behavior.

**Tech Stack:** Python 3.14, pytest-compatible tests, FastAPI planned, SQLite planned, static HTML/CSS/JavaScript shell.

## Global Constraints

- The project must run in mock mode without model API keys.
- The first version must be easy for a beginner to understand.
- The first version must support prompt templates, test cases, batch runs, automatic scoring, failure cases, version comparison, cost, and latency concepts.
- Do not mix this project with the existing RAG project in the parent directory.

---

### Task 1: Backend Core Evaluation Services

**Files:**
- Create: `backend/app/core/models.py`
- Create: `backend/app/services/prompt_renderer.py`
- Create: `backend/app/services/mock_model.py`
- Create: `backend/app/services/evaluator.py`
- Create: `backend/app/services/batch_runner.py`
- Test: `backend/tests/test_promptops_core.py`

**Interfaces:**
- Consumes: `PromptVersion`, `TestCase`
- Produces: `BatchRunSummary`, `EvaluationResult`, `ModelOutput`

- [x] **Step 1: Write failing tests**
- [x] **Step 2: Run tests and verify they fail for missing modules**
- [x] **Step 3: Implement minimal service code**
- [x] **Step 4: Run tests and verify they pass**

### Task 1.5: SQLite Repository and FastAPI Mock Run API

**Files:**
- Create: `backend/app/db/repository.py`
- Create: `backend/app/main.py`
- Test: `backend/tests/test_repository.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `run_batch`, `PromptVersion`, `TestCase`
- Produces: `GET /api/dashboard`, `GET /api/test-cases`, `GET /api/failure-cases`, `POST /api/runs/mock`

- [x] **Step 1: Write failing repository and API tests**
- [x] **Step 2: Run tests and verify they fail for missing modules**
- [x] **Step 3: Implement SQLite persistence and API routes**
- [x] **Step 4: Run tests and verify they pass**

### Task 2: Frontend Demonstration Shell

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/styles.css`
- Create: `frontend/app.js`

**Interfaces:**
- Consumes: static sample metrics matching backend concepts.
- Produces: HR-facing first screen explaining the workflow visually.

- [ ] **Step 1: Create a dashboard-first static page**
- [x] **Step 1: Create a dashboard-first static page**
- [x] **Step 2: Include sections for prompts, test cases, batch runs, scores, failures, and version comparison**
- [ ] **Step 3: Verify the HTML file can be opened locally**

### Task 3: Portfolio Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/demo_script.md`
- Create: `docs/resume_project.md`

**Interfaces:**
- Consumes: implemented MVP behavior and product design.
- Produces: materials for GitHub, screenshots, resume, and interview explanation.

- [x] **Step 1: Document architecture**
- [x] **Step 2: Write demo script**
- [x] **Step 3: Write resume and interview notes**
