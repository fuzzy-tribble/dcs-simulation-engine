# type: ignore
"""Make sure OpenRouter is accessible and returns valid responses."""

import pytest
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, BadRequestError, OpenAI, RateLimitError

load_dotenv()


def _require_no_exception(exc: Exception):
    pytest.fail(f"Unexpected exception from OpenRouter: {type(exc).__name__}: {exc}")


@pytest.fixture
def or_free_model_id():
    """A fixture that lets us query a free OpenRouter model to test the endpoint."""
    return "openai/gpt-oss-20b:free"


@pytest.mark.slow
def test_endpoint_accessible(client: OpenAI, or_free_model_id: str):
    """Smoke-test that the OpenRouter endpoint is reachable and returns models."""
    try:
        # List models; asserts we can hit the API and get a non-empty list.
        models = client.models.list(timeout=30)  # seconds
        assert hasattr(models, "data"), "No 'data' attribute on models list response."
        assert len(models.data) > 0, "OpenRouter returned an empty model list."

        # Optional: ensure our chosen model is present
        # (useful sanity check, not required)
        # ids = {m.id for m in models.data if getattr(m, "id", None)}
        # assert actor_model_id in ids, (
        #     f"Model '{actor_model_id}' not found in /models list. "
        #     f"Found {len(ids)} models."
        # )
    except (APIError, RateLimitError, APIConnectionError, BadRequestError) as e:
        _require_no_exception(e)


@pytest.mark.slow
def test_chat_completion_returns_message(client: OpenAI, or_free_model_id: str):
    """Ensure we can query the chosen model and receive a non-empty assistant message."""
    try:
        completion = client.chat.completions.create(
            model=or_free_model_id,
            messages=[{"role": "user", "content": "Say 'pong' and nothing else."}],
            timeout=60,  # seconds; avoid hanging the test suite
            # Optional but recommended for OpenRouter ranking/attribution:
            # extra_headers={"HTTP-Referer": "https://your-app", "X-Title": "Your App"},
        )

        # Basic structural assertions
        assert completion is not None, "No completion object returned."
        assert (
            hasattr(completion, "choices") and completion.choices
        ), "No choices returned."

        msg = completion.choices[0].message
        assert msg is not None, "No message in first choice."
        assert (
            getattr(msg, "role", None) == "assistant"
        ), "First message role is not 'assistant'."
        content = getattr(msg, "content", "")
        assert (
            isinstance(content, str) and content.strip()
        ), "Assistant content is empty."
    except (APIError, RateLimitError, APIConnectionError, BadRequestError) as e:
        _require_no_exception(e)
