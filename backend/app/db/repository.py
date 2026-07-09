import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from backend.app.core.models import BatchRunSummary, PromptVersion, TestCase
from backend.app.services.batch_runner import run_batch


class PromptOpsRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS prompt_templates (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    description TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY,
                    template_id INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    content TEXT NOT NULL,
                    change_note TEXT NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES prompt_templates(id)
                );

                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY,
                    input_text TEXT NOT NULL,
                    expected_keywords TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_version_id INTEGER NOT NULL,
                    total_cases INTEGER NOT NULL,
                    average_score REAL NOT NULL,
                    failure_count INTEGER NOT NULL,
                    total_cost_usd REAL NOT NULL,
                    average_latency_ms REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS model_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_run_id INTEGER NOT NULL,
                    test_case_id INTEGER NOT NULL,
                    rendered_prompt TEXT NOT NULL,
                    output_text TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    token_estimate INTEGER NOT NULL,
                    score REAL NOT NULL,
                    passed INTEGER NOT NULL,
                    score_reason TEXT NOT NULL,
                    human_score REAL,
                    human_note TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS failure_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_run_id INTEGER NOT NULL,
                    test_case_id INTEGER NOT NULL,
                    failure_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    analysis_note TEXT NOT NULL,
                    model_output_id INTEGER,
                    optimization_suggestion TEXT NOT NULL DEFAULT ''
                );
                """
            )
            self._ensure_column(connection, "model_outputs", "human_score", "REAL")
            self._ensure_column(
                connection,
                "model_outputs",
                "human_note",
                "TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(connection, "failure_cases", "model_output_id", "INTEGER")
            self._ensure_column(
                connection,
                "failure_cases",
                "optimization_suggestion",
                "TEXT NOT NULL DEFAULT ''",
            )

    def seed_demo_data(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO prompt_templates (id, name, task_type, description)
                VALUES (1, '客服问答 Prompt', 'support_qa', '用简洁准确的方式回答客服问题。')
                """
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO prompt_versions (id, template_id, label, content, change_note)
                VALUES (1, 1, 'v1', '你是一名专业的客服助手。请回答用户问题：{{user_input}}', '初始 Prompt 版本。')
                """
            )
            cases = [
                (1, "如何重置登录密码？", ["重置", "密码"]),
                (2, "如何申请年假？", ["年假", "直属主管"]),
                (3, "报销流程是什么？", ["发票", "财务", "审批"]),
            ]
            for case_id, input_text, expected_keywords in cases:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO test_cases (id, input_text, expected_keywords)
                    VALUES (?, ?, ?)
                    """,
                    (case_id, input_text, json.dumps(expected_keywords)),
                )

    def reset_demo_data(self) -> None:
        with self._connection() as connection:
            for table_name in [
                "failure_cases",
                "model_outputs",
                "test_runs",
                "prompt_versions",
                "prompt_templates",
                "test_cases",
            ]:
                connection.execute(f"DELETE FROM {table_name}")
            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name IN ('test_runs', 'model_outputs', 'failure_cases')
                """
            )
        self.seed_demo_data()

    def get_prompt_version(self, version_id: int) -> PromptVersion:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id, template_id, label, content, change_note
                FROM prompt_versions
                WHERE id = ?
                """,
                (version_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Prompt version {version_id} does not exist.")
        return PromptVersion(
            id=row["id"],
            template_id=row["template_id"],
            label=row["label"],
            content=row["content"],
            change_note=row["change_note"],
        )

    def list_prompt_versions(self) -> list[PromptVersion]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, template_id, label, content, change_note
                FROM prompt_versions
                ORDER BY id
                """
            ).fetchall()
        return [
            PromptVersion(
                id=row["id"],
                template_id=row["template_id"],
                label=row["label"],
                content=row["content"],
                change_note=row["change_note"],
            )
            for row in rows
        ]

    def create_prompt_version(
        self,
        template_id: int,
        label: str,
        content: str,
        change_note: str,
    ) -> PromptVersion:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO prompt_versions (template_id, label, content, change_note)
                VALUES (?, ?, ?, ?)
                """,
                (template_id, label, content, change_note),
            )
            version_id = cursor.lastrowid
        return self.get_prompt_version(version_id)

    def update_prompt_version(
        self,
        version_id: int,
        label: str,
        content: str,
        change_note: str,
    ) -> PromptVersion:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE prompt_versions
                SET label = ?, content = ?, change_note = ?
                WHERE id = ?
                """,
                (label, content, change_note, version_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Prompt version {version_id} does not exist.")
        return self.get_prompt_version(version_id)

    def list_test_cases(self) -> list[TestCase]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, input_text, expected_keywords
                FROM test_cases
                ORDER BY id
                """
            ).fetchall()
        return [
            TestCase(
                id=row["id"],
                input_text=row["input_text"],
                expected_keywords=json.loads(row["expected_keywords"]),
            )
            for row in rows
        ]

    def create_test_case(
        self,
        input_text: str,
        expected_keywords: list[str],
    ) -> TestCase:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO test_cases (input_text, expected_keywords)
                VALUES (?, ?)
                """,
                (input_text, json.dumps(expected_keywords)),
            )
            case_id = cursor.lastrowid
        return self.get_test_case(case_id)

    def update_test_case(
        self,
        case_id: int,
        input_text: str,
        expected_keywords: list[str],
    ) -> TestCase:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE test_cases
                SET input_text = ?, expected_keywords = ?
                WHERE id = ?
                """,
                (input_text, json.dumps(expected_keywords), case_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Test case {case_id} does not exist.")
        return self.get_test_case(case_id)

    def get_test_case(self, case_id: int) -> TestCase:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id, input_text, expected_keywords
                FROM test_cases
                WHERE id = ?
                """,
                (case_id,),
            ).fetchone()
        if row is None:
            raise ValueError(f"Test case {case_id} does not exist.")
        return TestCase(
            id=row["id"],
            input_text=row["input_text"],
            expected_keywords=json.loads(row["expected_keywords"]),
        )

    def create_batch_run(
        self,
        version: PromptVersion,
        test_cases: list[TestCase],
    ) -> BatchRunSummary:
        summary = run_batch(version, test_cases)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO test_runs (
                    prompt_version_id,
                    total_cases,
                    average_score,
                    failure_count,
                    total_cost_usd,
                    average_latency_ms
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    version.id,
                    summary.total_cases,
                    summary.average_score,
                    summary.failure_count,
                    summary.total_cost_usd,
                    summary.average_latency_ms,
                ),
            )
            run_id = cursor.lastrowid
            for item in summary.items:
                output_cursor = connection.execute(
                    """
                    INSERT INTO model_outputs (
                        test_run_id,
                        test_case_id,
                        rendered_prompt,
                        output_text,
                        latency_ms,
                        cost_usd,
                        token_estimate,
                        score,
                        passed,
                        score_reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        item.test_case.id,
                        item.rendered_prompt,
                        item.output.text,
                        item.output.latency_ms,
                        item.output.cost_usd,
                        item.output.token_estimate,
                        item.evaluation.score,
                        1 if item.evaluation.passed else 0,
                        item.evaluation.reason,
                    ),
                )
                object.__setattr__(item, "output_id", output_cursor.lastrowid)
                if not item.evaluation.passed:
                    connection.execute(
                        """
                        INSERT INTO failure_cases (
                            test_run_id,
                            test_case_id,
                            failure_type,
                            severity,
                            analysis_note,
                            model_output_id,
                            optimization_suggestion
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            run_id,
                            item.test_case.id,
                            "keyword_miss",
                            "high" if item.evaluation.score < 0.5 else "medium",
                            item.evaluation.reason,
                            item.output_id,
                            "补充缺失关键词，或在 Prompt 中明确要求覆盖所有期望要点。",
                        ),
                    )
        return summary

    def update_human_review(
        self,
        output_id: int,
        human_score: float,
        human_note: str,
    ) -> dict[str, object]:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE model_outputs
                SET human_score = ?, human_note = ?
                WHERE id = ?
                """,
                (human_score, human_note, output_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Model output {output_id} does not exist.")
            row = connection.execute(
                """
                SELECT
                    id,
                    test_run_id,
                    test_case_id,
                    output_text,
                    score,
                    passed,
                    score_reason,
                    human_score,
                    human_note
                FROM model_outputs
                WHERE id = ?
                """,
                (output_id,),
            ).fetchone()
        return dict(row)

    def get_dashboard_metrics(self) -> dict[str, int | float]:
        with self._connection() as connection:
            run_row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_runs,
                    COALESCE(AVG(average_score), 0) AS average_score,
                    COALESCE(SUM(failure_count), 0) AS total_failures,
                    COALESCE(SUM(total_cases), 0) AS total_cases,
                    COALESCE(SUM(total_cost_usd), 0) AS total_cost_usd,
                    COALESCE(AVG(average_latency_ms), 0) AS average_latency_ms
                FROM test_runs
                """
            ).fetchone()
            case_row = connection.execute(
                "SELECT COUNT(*) AS total_test_cases FROM test_cases"
            ).fetchone()

        total_cases = run_row["total_cases"]
        total_failures = run_row["total_failures"]
        failure_rate = round(total_failures / total_cases, 2) if total_cases else 0
        return {
            "total_runs": run_row["total_runs"],
            "total_test_cases": case_row["total_test_cases"],
            "average_score": round(run_row["average_score"], 2),
            "failure_rate": failure_rate,
            "total_cost_usd": round(run_row["total_cost_usd"], 6),
            "average_latency_ms": round(run_row["average_latency_ms"], 2),
        }

    def list_failure_cases(self) -> list[dict[str, str | int]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    fc.id,
                    fc.test_run_id,
                    fc.test_case_id,
                    fc.failure_type,
                    fc.severity,
                    fc.analysis_note,
                    fc.optimization_suggestion,
                    tc.input_text AS test_input,
                    mo.output_text AS output_text,
                    mo.score AS score,
                    mo.score_reason AS score_reason
                FROM failure_cases fc
                JOIN test_cases tc ON tc.id = fc.test_case_id
                LEFT JOIN model_outputs mo ON mo.id = fc.model_output_id
                ORDER BY fc.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_prompt_version_comparison(self) -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    pv.id AS prompt_version_id,
                    pv.label AS label,
                    pv.change_note AS change_note,
                    COUNT(tr.id) AS run_count,
                    COALESCE(SUM(tr.total_cases), 0) AS total_cases,
                    COALESCE(SUM(tr.failure_count), 0) AS failure_count,
                    COALESCE(AVG(tr.average_score), 0) AS average_score,
                    COALESCE(SUM(tr.total_cost_usd), 0) AS total_cost_usd,
                    COALESCE(AVG(tr.average_latency_ms), 0) AS average_latency_ms
                FROM prompt_versions pv
                LEFT JOIN test_runs tr ON tr.prompt_version_id = pv.id
                GROUP BY pv.id, pv.label, pv.change_note
                ORDER BY pv.id
                """
            ).fetchall()

        comparison = []
        for row in rows:
            total_cases = row["total_cases"]
            failure_count = row["failure_count"]
            comparison.append(
                {
                    "prompt_version_id": row["prompt_version_id"],
                    "label": row["label"],
                    "change_note": row["change_note"],
                    "run_count": row["run_count"],
                    "total_cases": total_cases,
                    "failure_count": failure_count,
                    "failure_rate": round(failure_count / total_cases, 2)
                    if total_cases
                    else 0,
                    "average_score": round(row["average_score"], 2),
                    "total_cost_usd": round(row["total_cost_usd"], 6),
                    "average_latency_ms": round(row["average_latency_ms"], 2),
                }
            )
        return comparison

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        definition: str,
    ) -> None:
        columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if column_name not in {column["name"] for column in columns}:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
            )
