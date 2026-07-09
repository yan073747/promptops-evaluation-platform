import tempfile
import unittest
from pathlib import Path

from backend.app.db.repository import PromptOpsRepository


class PromptOpsRepositoryTests(unittest.TestCase):
    def test_seed_demo_data_creates_prompt_version_and_test_cases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            repo = PromptOpsRepository(db_path)

            repo.initialize()
            repo.seed_demo_data()

            version = repo.get_prompt_version(1)
            cases = repo.list_test_cases()

            self.assertEqual(version.label, "v1")
            self.assertIn("{{user_input}}", version.content)
            self.assertGreaterEqual(len(cases), 3)

    def test_save_batch_run_persists_metrics_and_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "promptops.db"
            repo = PromptOpsRepository(db_path)
            repo.initialize()
            repo.seed_demo_data()
            version = repo.get_prompt_version(1)
            cases = repo.list_test_cases()

            run = repo.create_batch_run(version, cases)
            dashboard = repo.get_dashboard_metrics()
            failures = repo.list_failure_cases()

            self.assertEqual(run.total_cases, len(cases))
            self.assertEqual(dashboard["total_runs"], 1)
            self.assertGreater(dashboard["average_score"], 0)
            self.assertIn("failure_rate", dashboard)
            self.assertIsInstance(failures, list)


if __name__ == "__main__":
    unittest.main()
