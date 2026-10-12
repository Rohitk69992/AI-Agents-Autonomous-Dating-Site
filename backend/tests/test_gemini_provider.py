import json
import pytest
from unittest.mock import MagicMock, patch

from app.llm.provider import (
    GeminiLLMProvider,
    DEFAULT_GEMINI_CANDIDATE_MODELS,
    get_llm_provider
)
from app.core.config import settings


class MockUsageMetadata:
    def __init__(self, prompt_tokens: int = 150, candidates_tokens: int = 80):
        self.prompt_token_count = prompt_tokens
        self.candidates_token_count = candidates_tokens


class MockResponse:
    def __init__(self, text: str, prompt_tokens: int = 150, candidates_tokens: int = 80):
        self.text = text
        self.usage_metadata = MockUsageMetadata(prompt_tokens, candidates_tokens)


def test_gemini_provider_requires_api_key():
    with pytest.raises(ValueError) as exc:
        GeminiLLMProvider(api_key="")
    assert "GEMINI_API_KEY must be provided" in str(exc.value)


def test_gemini_provider_model_name_normalization():
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
        provider = GeminiLLMProvider(api_key="test-key", model_name="models/gemini-2.5-flash")
        assert provider.model_name == "gemini-2.5-flash"

        provider2 = GeminiLLMProvider(api_key="test-key", model_name="gemini-2.0-flash")
        assert provider2.model_name == "gemini-2.0-flash"


def test_gemini_successful_generation():
    fake_json = {
        "internal_thought": "Thinking about outdoor hobbies",
        "message": "I love hiking too! What is your favorite trail?"
    }
    mock_resp = MockResponse(text=json.dumps(fake_json), prompt_tokens=120, candidates_tokens=65)

    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as MockModel:
        
        instance = MagicMock()
        instance.generate_content.return_value = mock_resp
        MockModel.return_value = instance

        provider = GeminiLLMProvider(api_key="test-key", model_name="gemini-2.5-flash")
        result = provider.generate(
            system_prompt="You are a dating agent",
            user_prompt="Say hello",
            response_schema={"type": "object"}
        )

        assert result.provider == "gemini"
        assert result.model == "gemini-2.5-flash"
        assert result.tokens_input == 120
        assert result.tokens_output == 65
        assert result.tokens_total == 185
        assert result.cost_usd > 0
        assert result.structured_data == fake_json


def test_gemini_404_failover_without_retrying_same_model():
    """
    When primary model (gemini-2.5-flash) returns 404, provider should NOT retry it,
    and should immediately succeed with the next candidate (gemini-2.0-flash).
    """
    call_counts = {}

    def side_effect_generate(prompt):
        # Inspect which model is currently being generated
        current_model = getattr(side_effect_generate, "current_model", None)
        call_counts[current_model] = call_counts.get(current_model, 0) + 1
        if current_model == "gemini-2.5-flash":
            raise Exception("404 models/gemini-2.5-flash not found for API version v1beta, or is not supported for generateContent.")
        return MockResponse(text=json.dumps({"message": "Hello from 2.0-flash"}))

    def mock_model_init(model_name, **kwargs):
        side_effect_generate.current_model = model_name
        m = MagicMock()
        m.generate_content.side_effect = side_effect_generate
        return m

    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel", side_effect=mock_model_init):

        provider = GeminiLLMProvider(api_key="test-key", model_name="gemini-2.5-flash")
        result = provider.generate(
            system_prompt="You are a dating agent",
            user_prompt="Say hello",
            response_schema={"type": "object"}
        )

        # gemini-2.5-flash should have been called EXACTLY ONCE (no retry on 404!)
        assert call_counts["gemini-2.5-flash"] == 1
        # gemini-2.0-flash was called and succeeded
        assert call_counts["gemini-2.0-flash"] == 1
        assert result.model == "gemini-2.0-flash"
        assert result.structured_data == {"message": "Hello from 2.0-flash"}


def test_gemini_transient_error_retries_with_backoff(monkeypatch):
    """
    When primary model encounters transient 429/quota error, it retries on the same model.
    """
    attempts = 0
    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    def side_effect_generate(prompt):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise Exception("429 Resource has been exhausted (rate limit)")
        return MockResponse(text=json.dumps({"message": "Success on attempt 2"}))

    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as MockModel:

        instance = MagicMock()
        instance.generate_content.side_effect = side_effect_generate
        MockModel.return_value = instance

        provider = GeminiLLMProvider(api_key="test-key", model_name="gemini-2.5-flash")
        result = provider.generate(
            system_prompt="Agent prompt",
            user_prompt="Say something",
            response_schema={"type": "object"}
        )

        assert attempts == 2
        assert len(sleeps) == 1
        assert sleeps[0] == 1.0
        assert result.model == "gemini-2.5-flash"
        assert result.structured_data == {"message": "Success on attempt 2"}


def test_gemini_all_candidates_exhausted_raises_actionable_error(monkeypatch):
    """
    When all candidates fail, RuntimeError is raised summarizing attempts across models.
    Ensure API keys are never leaked in error messages.
    """
    monkeypatch.setattr("time.sleep", lambda s: None)

    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel") as MockModel, \
         patch("google.generativeai.list_models", return_value=[]):

        instance = MagicMock()
        instance.generate_content.side_effect = Exception("404 models/not-found?key=AIzaSySecretApiKey123456789012345678901")
        MockModel.return_value = instance

        provider = GeminiLLMProvider(api_key="AIzaSySecretApiKey123456789012345678901", model_name="gemini-2.5-flash")
        
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate("System", "User")

        err_msg = str(exc_info.value)
        assert "Gemini generation failed after attempts across" in err_msg
        assert "gemini-2.5-flash" in err_msg
        assert "gemini-2.0-flash" in err_msg
        # Check that secret API key was redacted
        assert "AIzaSySecretApiKey123456789012345678901" not in err_msg
        assert "[REDACTED" in err_msg


def test_gemini_dynamic_model_discovery_fallback():
    """
    If all static candidate models fail with 404, dynamic discovery via list_models() finds
    and uses an available model.
    """
    class MockDiscoveredModel:
        def __init__(self, name):
            self.name = name
            self.supported_generation_methods = ["generateContent"]

    def mock_model_init(model_name, **kwargs):
        m = MagicMock()
        if model_name in DEFAULT_GEMINI_CANDIDATE_MODELS:
            m.generate_content.side_effect = Exception(f"404 models/{model_name} not found")
        elif model_name == "gemini-future-flash":
            m.generate_content.return_value = MockResponse(text=json.dumps({"discovered": True}))
        return m

    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel", side_effect=mock_model_init), \
         patch("google.generativeai.list_models", return_value=[
             MockDiscoveredModel("models/gemini-future-flash"),
             MockDiscoveredModel("models/embedding-001")  # Not generateContent
         ]):

        provider = GeminiLLMProvider(api_key="test-key", model_name="gemini-2.5-flash")
        result = provider.generate(
            system_prompt="System",
            user_prompt="User",
            response_schema={"type": "object"}
        )

        assert result.model == "gemini-future-flash"
        assert result.structured_data == {"discovered": True}


def test_json_extraction_formats():
    with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
        provider = GeminiLLMProvider(api_key="test-key")

        # Clean JSON
        assert provider._extract_json('{"key": "value"}') == {"key": "value"}

        # Markdown wrapped JSON
        markdown_text = "Here is the response:\n```json\n{\"score\": 8.5}\n```\nHope it helps!"
        assert provider._extract_json(markdown_text) == {"score": 8.5}

        # Text with raw JSON embedded
        mixed_text = "Analysis complete: {\"passed\": true, \"count\": 3} End of message."
        assert provider._extract_json(mixed_text) == {"passed": True, "count": 3}

        # Empty or invalid
        assert provider._extract_json("") is None
        assert provider._extract_json("Not a json at all") is None
