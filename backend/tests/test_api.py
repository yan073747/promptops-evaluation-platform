import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


class PromptOpsApiTests(unittest.TestCase):
    def test_dashboard_starts_with_demo_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)

            response = client.get("/api/dashboard")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["total_runs"], 0)
            self.assertEqual(payload["total_test_cases"], 3)

    def test_root_serves_frontend_shell(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn("PromptOps 评测与优化平台", response.text)

    def test_demo_test_cases_use_chinese_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)

            response = client.get("/api/test-cases")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("如何重置登录密码？", [item["input_text"] for item in payload])

    def test_run_batch_endpoint_creates_mock_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)

            response = client.post("/api/runs/mock", json={"prompt_version_id": 1})

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["total_cases"], 3)
            self.assertGreater(payload["total_cost_usd"], 0)
            self.assertEqual(len(payload["items"]), 3)
            self.assertIn("output_id", payload["items"][0])

    def test_update_model_output_human_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)
            run_response = client.post("/api/runs/mock", json={"prompt_version_id": 1})
            output_id = run_response.json()["items"][0]["output_id"]

            review_response = client.put(
                f"/api/model-outputs/{output_id}/human-review",
                json={
                    "human_score": 0.8,
                    "human_note": "答案可用，但还可以更具体。",
                },
            )

            self.assertEqual(review_response.status_code, 200)
            payload = review_response.json()
            self.assertEqual(payload["id"], output_id)
            self.assertEqual(payload["human_score"], 0.8)
            self.assertEqual(payload["human_note"], "答案可用，但还可以更具体。")

    def test_create_and_update_prompt_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)

            create_response = client.post(
                "/api/prompt-versions",
                json={
                    "template_id": 1,
                    "label": "v2",
                    "content": "请用三点回答：{{user_input}}",
                    "change_note": "增加格式要求",
                },
            )
            created = create_response.json()
            update_response = client.put(
                f"/api/prompt-versions/{created['id']}",
                json={
                    "label": "v2.1",
                    "content": "请用三点回答，并给出下一步建议：{{user_input}}",
                    "change_note": "补充下一步建议",
                },
            )

            list_response = client.get("/api/prompt-versions")

            self.assertEqual(create_response.status_code, 200)
            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(update_response.json()["label"], "v2.1")
            self.assertIn("下一步建议", update_response.json()["content"])
            self.assertIn("v2.1", [item["label"] for item in list_response.json()])

    def test_create_and_update_test_case(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)

            create_response = client.post(
                "/api/test-cases",
                json={
                    "input_text": "如何修改绑定手机号？",
                    "expected_keywords": ["手机号", "验证"],
                },
            )
            created = create_response.json()
            update_response = client.put(
                f"/api/test-cases/{created['id']}",
                json={
                    "input_text": "如何修改账号绑定手机号？",
                    "expected_keywords": ["账号", "手机号", "验证"],
                },
            )

            list_response = client.get("/api/test-cases")

            self.assertEqual(create_response.status_code, 200)
            self.assertEqual(update_response.status_code, 200)
            self.assertEqual(update_response.json()["input_text"], "如何修改账号绑定手机号？")
            self.assertEqual(update_response.json()["expected_keywords"], ["账号", "手机号", "验证"])
            self.assertIn("如何修改账号绑定手机号？", [item["input_text"] for item in list_response.json()])

    def test_prompt_version_comparison_uses_real_run_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)
            created = client.post(
                "/api/prompt-versions",
                json={
                    "template_id": 1,
                    "label": "v2",
                    "content": "Answer with three bullet points: {{user_input}}",
                    "change_note": "Add structure",
                },
            ).json()

            client.post("/api/runs/mock", json={"prompt_version_id": 1})
            client.post("/api/runs/mock", json={"prompt_version_id": created["id"]})

            response = client.get("/api/prompt-version-comparison")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertGreaterEqual(len(payload), 2)
            labels = [item["label"] for item in payload]
            self.assertIn("v1", labels)
            self.assertIn("v2", labels)
            v2 = next(item for item in payload if item["label"] == "v2")
            self.assertEqual(v2["run_count"], 1)
            self.assertGreater(v2["total_cost_usd"], 0)
            self.assertIn("failure_rate", v2)

    def test_failure_case_analysis_uses_failed_output_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)
            client.post(
                "/api/test-cases",
                json={
                    "input_text": "故意失败：会员退款到账时间是多少？",
                    "expected_keywords": ["退款", "到账", "3个工作日"],
                },
            )

            run_response = client.post("/api/runs/mock", json={"prompt_version_id": 1})
            failures_response = client.get("/api/failure-cases")

            self.assertEqual(run_response.status_code, 200)
            self.assertGreater(run_response.json()["failure_count"], 0)
            self.assertEqual(failures_response.status_code, 200)
            failures = failures_response.json()
            self.assertGreater(len(failures), 0)
            first = failures[0]
            self.assertIn("test_input", first)
            self.assertIn("output_text", first)
            self.assertIn("score", first)
            self.assertIn("optimization_suggestion", first)
            self.assertEqual(first["failure_type"], "keyword_miss")
            self.assertEqual(first["severity"], "high")

    def test_demo_reset_restores_clean_seed_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            app = create_app(db_path)
            client = TestClient(app)
            created = client.post(
                "/api/prompt-versions",
                json={
                    "template_id": 1,
                    "label": "v2",
                    "content": "Answer with structure: {{user_input}}",
                    "change_note": "Temporary demo version",
                },
            ).json()
            client.post(
                "/api/test-cases",
                json={
                    "input_text": "故意失败：会员退款到账时间是多少？",
                    "expected_keywords": ["退款", "到账", "3个工作日"],
                },
            )
            client.post("/api/runs/mock", json={"prompt_version_id": created["id"]})

            reset_response = client.post("/api/demo/reset")

            self.assertEqual(reset_response.status_code, 200)
            self.assertEqual(reset_response.json()["status"], "reset")
            dashboard = client.get("/api/dashboard").json()
            prompt_versions = client.get("/api/prompt-versions").json()
            failures = client.get("/api/failure-cases").json()
            comparison = client.get("/api/prompt-version-comparison").json()
            self.assertEqual(dashboard["total_runs"], 0)
            self.assertEqual(dashboard["total_test_cases"], 3)
            self.assertEqual([item["label"] for item in prompt_versions], ["v1"])
            self.assertEqual(failures, [])
            self.assertEqual(comparison[0]["run_count"], 0)


if __name__ == "__main__":
    unittest.main()
