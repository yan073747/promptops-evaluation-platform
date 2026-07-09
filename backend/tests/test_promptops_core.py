import unittest

from backend.app.core.models import PromptVersion, TestCase
from backend.app.services.batch_runner import run_batch
from backend.app.services.evaluator import score_output
from backend.app.services.mock_model import generate_mock_output
from backend.app.services.prompt_renderer import render_prompt


class PromptOpsCoreTests(unittest.TestCase):
    def test_render_prompt_replaces_user_input_placeholder(self):
        version = PromptVersion(
            id=1,
            template_id=1,
            label="v1",
            content="You are a support agent. Answer this: {{user_input}}",
            change_note="Initial version",
        )
        case = TestCase(
            id=1,
            input_text="How do I reset my password?",
            expected_keywords=["reset", "password"],
        )

        rendered = render_prompt(version, case)

        self.assertNotIn("{{user_input}}", rendered)
        self.assertIn("How do I reset my password?", rendered)

    def test_mock_model_returns_deterministic_answer_with_expected_keywords(self):
        case = TestCase(
            id=2,
            input_text="How do I request annual leave?",
            expected_keywords=["annual leave", "manager"],
        )

        output = generate_mock_output(case)

        self.assertIn("annual leave", output.text)
        self.assertIn("manager", output.text)
        self.assertGreater(output.latency_ms, 0)
        self.assertGreater(output.cost_usd, 0)

    def test_score_output_uses_expected_keyword_hit_ratio(self):
        case = TestCase(
            id=3,
            input_text="What is the refund process?",
            expected_keywords=["refund", "receipt", "7 days"],
        )

        result = score_output("Please keep your receipt. Returns finish within 7 days.", case)

        self.assertEqual(result.score, 0.67)
        self.assertFalse(result.passed)
        self.assertIn("2/3", result.reason)

    def test_batch_run_collects_scores_failures_cost_and_latency(self):
        version = PromptVersion(
            id=4,
            template_id=1,
            label="v1",
            content="Answer carefully: {{user_input}}",
            change_note="Initial version",
        )
        cases = [
            TestCase(
                id=10,
                input_text="How do I reset my password?",
                expected_keywords=["reset", "password"],
            ),
            TestCase(
                id=11,
                input_text="What is the reimbursement process?",
                expected_keywords=["invoice", "finance", "approval"],
            ),
        ]

        summary = run_batch(version, cases)

        self.assertEqual(summary.total_cases, 2)
        self.assertEqual(len(summary.items), 2)
        self.assertGreaterEqual(summary.average_score, 0)
        self.assertGreater(summary.total_cost_usd, 0)
        self.assertGreater(summary.average_latency_ms, 0)
        self.assertGreaterEqual(summary.failure_count, 0)


if __name__ == "__main__":
    unittest.main()
