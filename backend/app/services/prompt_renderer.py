from backend.app.core.models import PromptVersion, TestCase


def render_prompt(version: PromptVersion, test_case: TestCase) -> str:
    return version.content.replace("{{user_input}}", test_case.input_text)

