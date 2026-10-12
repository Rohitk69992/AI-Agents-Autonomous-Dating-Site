import json
import pytest
from unittest.mock import MagicMock, patch

from app.llm.provider import (
    GroqLLMProvider,
    DEFAULT_GROQ_CANDIDATE_MODELS,
    get_llm_provider
)
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import Participant, AnalyzedProfile, DatingSession, ConversationMessage, AgentEvaluation
from app.dating.harness import execute_dating_session
from app.ranking.engine import calculate_rankings_for_participant


class MockChoiceMessage:
    def __init__(self, content: str):
        self.content = content


class MockChoice:
    def __init__(self, content: str):
        self.message = MockChoiceMessage(content)


class MockUsage:
    def __init__(self, prompt_tokens: int = 140, completion_tokens: int = 90):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens


class MockGroqCompletion:
    def __init__(self, content: str, prompt_tokens: int = 140, completion_tokens: int = 90):
        self.choices = [MockChoice(content)]
        self.usage = MockUsage(prompt_tokens, completion_tokens)


def test_groq_provider_requires_api_key():
    with pytest.raises(ValueError) as exc:
        GroqLLMProvider(api_key="")
    assert "GROQ_API_KEY must be provided" in str(exc.value)


def test_strict_groq_mode_raises_when_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    with pytest.raises(RuntimeError) as exc:
        get_llm_provider()
    assert "LLM_PROVIDER is configured as 'groq', but no GROQ_API_KEY" in str(exc.value)


def test_groq_successful_text_generation():
    fake_json = {
        "internal_thought": "I notice my date shares a passion for rock climbing.",
        "decision_summary": "Inquiring about favorite climbing spots.",
        "decision_factors": ["Shared interest: climbing"],
        "message": "It is great to meet you! Do you prefer indoor bouldering or outdoor lead climbing?",
        "question_asked": "Do you prefer indoor bouldering or outdoor lead climbing?",
        "interest_referenced": "Rock climbing"
    }
    mock_completion = MockGroqCompletion(
        content=json.dumps(fake_json),
        prompt_tokens=200,
        completion_tokens=85
    )

    with patch("groq.Groq") as MockGroq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.return_value = mock_completion
        MockGroq.return_value = client_instance

        provider = GroqLLMProvider(api_key="gsk_valid_test_key", model_name="openai/gpt-oss-20b")
        result = provider.generate(
            system_prompt="You are a dating agent",
            user_prompt="Generate turn",
            response_schema={"type": "object"}
        )

        assert result.provider == "groq"
        assert result.model == "openai/gpt-oss-20b"
        assert result.tokens_input == 200
        assert result.tokens_output == 85
        assert result.tokens_total == 285
        assert result.cost_usd > 0
        assert result.structured_data == fake_json

        # Verify max_completion_tokens was used in client call
        called_kwargs = client_instance.chat.completions.create.call_args.kwargs
        assert "max_completion_tokens" in called_kwargs
        assert called_kwargs["max_completion_tokens"] <= 4096


def test_groq_404_failover_without_retrying_same_model():
    """
    When primary model (openai/gpt-oss-20b) returns 404, provider must not retry it,
    and must immediately fall back to the next candidate (openai/gpt-oss-120b).
    """
    call_counts = {}

    def side_effect_create(**kwargs):
        model = kwargs.get("model")
        call_counts[model] = call_counts.get(model, 0) + 1
        if model == "openai/gpt-oss-20b":
            err = Exception("404 The model 'openai/gpt-oss-20b' does not exist or you do not have access to it.")
            setattr(err, "status_code", 404)
            raise err
        return MockGroqCompletion(content=json.dumps({"message": "Hello from 120B"}))

    with patch("groq.Groq") as MockGroq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = side_effect_create
        MockGroq.return_value = client_instance

        provider = GroqLLMProvider(api_key="gsk_test_key", model_name="openai/gpt-oss-20b")
        result = provider.generate(
            system_prompt="System",
            user_prompt="Say hi",
            response_schema={"type": "object"}
        )

        # openai/gpt-oss-20b should be attempted EXACTLY ONCE (no retry on 404)
        assert call_counts["openai/gpt-oss-20b"] == 1
        assert call_counts["openai/gpt-oss-120b"] == 1
        assert result.model == "openai/gpt-oss-120b"
        assert result.structured_data == {"message": "Hello from 120B"}


def test_groq_transient_error_retries_with_backoff(monkeypatch):
    """
    When primary model encounters transient 429 rate limit, it retries on the same model.
    """
    attempts = 0
    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    def side_effect_create(**kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            err = Exception("429 Rate limit reached for model openai/gpt-oss-20b.")
            setattr(err, "status_code", 429)
            raise err
        return MockGroqCompletion(content=json.dumps({"message": "Success on retry"}))

    with patch("groq.Groq") as MockGroq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = side_effect_create
        MockGroq.return_value = client_instance

        provider = GroqLLMProvider(api_key="gsk_test_key", model_name="openai/gpt-oss-20b")
        result = provider.generate(
            system_prompt="System",
            user_prompt="User",
            response_schema={"type": "object"}
        )

        assert attempts == 2
        assert len(sleeps) == 1
        assert sleeps[0] == 1.0
        assert result.structured_data == {"message": "Success on retry"}


def test_groq_token_limit_error_skips_without_retry():
    """
    When a model rejects request because token limit exceeded, provider must not retry it,
    and must skip immediately to the next candidate model.
    """
    call_counts = {}

    def side_effect_create(**kwargs):
        model = kwargs.get("model")
        call_counts[model] = call_counts.get(model, 0) + 1
        if model == "openai/gpt-oss-20b":
            err = Exception("400 max_tokens cannot exceed the model limit of 512")
            setattr(err, "status_code", 400)
            raise err
        return MockGroqCompletion(content=json.dumps({"message": "Success on fallback model"}))

    with patch("groq.Groq") as MockGroq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = side_effect_create
        MockGroq.return_value = client_instance

        provider = GroqLLMProvider(api_key="gsk_test_key", model_name="openai/gpt-oss-20b")
        result = provider.generate("System", "User", response_schema={"type": "object"})

        # openai/gpt-oss-20b attempted exactly once (no retry on token limit error)
        assert call_counts["openai/gpt-oss-20b"] == 1
        assert call_counts["openai/gpt-oss-120b"] == 1
        assert result.model == "openai/gpt-oss-120b"
        assert result.structured_data == {"message": "Success on fallback model"}


def test_groq_quota_exhaustion_sanitizes_api_keys(monkeypatch):
    """
    When all models fail with quota errors, ensure error diagnostics summarize all models
    and GROQ_API_KEY is never leaked.
    """
    monkeypatch.setattr("time.sleep", lambda s: None)

    with patch("groq.Groq") as MockGroq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = Exception(
            "429 Quota exhausted for api_key=gsk_SecretGroqKey1234567890abcdef"
        )
        client_instance.models.list.return_value = MagicMock(data=[])
        MockGroq.return_value = client_instance

        provider = GroqLLMProvider(api_key="gsk_SecretGroqKey1234567890abcdef")

        with pytest.raises(RuntimeError) as exc:
            provider.generate("System", "User")

        err_msg = str(exc.value)
        assert "Groq generation failed after attempts across" in err_msg
        assert "openai/gpt-oss-20b" in err_msg
        assert "openai/gpt-oss-120b" in err_msg
        assert "gsk_SecretGroqKey1234567890abcdef" not in err_msg
        assert "[REDACTED" in err_msg


def test_groq_dynamic_discovery_excludes_prompt_guard():
    """
    When static candidate models return 404, dynamic discovery excludes Prompt Guard
    and other non-chat models, selecting only supported chat models.
    """
    class MockModelItem:
        def __init__(self, model_id: str):
            self.id = model_id

    called_models = []

    def side_effect_create(**kwargs):
        model = kwargs.get("model")
        called_models.append(model)
        if model in DEFAULT_GROQ_CANDIDATE_MODELS:
            err = Exception(f"404 Model '{model}' not found.")
            setattr(err, "status_code", 404)
            raise err
        elif model == "openai/gpt-oss-20b-dynamic":
            return MockGroqCompletion(content=json.dumps({"discovered": True}))
        raise Exception(f"Unexpected model call: {model}")

    with patch("groq.Groq") as MockGroq:
        client_instance = MagicMock()
        client_instance.chat.completions.create.side_effect = side_effect_create
        client_instance.models.list.return_value = MagicMock(data=[
            MockModelItem("meta-llama/llama-prompt-guard-2-22m"),  # Must be skipped
            MockModelItem("meta-llama/llama-prompt-guard-2-86m"),  # Must be skipped
            MockModelItem("whisper-large-v3"),                    # Must be skipped
            MockModelItem("openai/gpt-oss-20b-dynamic"),          # Chat model: accepted!
        ])
        MockGroq.return_value = client_instance

        provider = GroqLLMProvider(api_key="gsk_test_key", model_name="openai/gpt-oss-20b")
        result = provider.generate("System", "User", response_schema={"type": "object"})

        # Prompt Guard models must NEVER have been called
        assert "meta-llama/llama-prompt-guard-2-22m" not in called_models
        assert "meta-llama/llama-prompt-guard-2-86m" not in called_models
        assert "whisper-large-v3" not in called_models

        assert result.model == "openai/gpt-oss-20b-dynamic"
        assert result.structured_data == {"discovered": True}


def test_groq_alternating_multi_turn_dating_dialogue_and_persistence(monkeypatch):
    """
    End-to-end test of dating simulation with Groq provider:
    - Validates Agent A opens (turn 1).
    - Validates Agent B responds with context preservation (turn 2).
    - Validates turns alternate and history is preserved.
    - Validates database persistence of messages, evaluations, and rankings.
    """
    import uuid
    db = SessionLocal()
    test_uid = uuid.uuid4().hex[:8]
    p_a_id = f"part-groq-a-{test_uid}"
    p_b_id = f"part-groq-b-{test_uid}"
    sess_id = f"session-groq-{test_uid}"
    try:
        # Create 2 consenting test participants with handles
        p_a = Participant(
            id=p_a_id,
            name="Alice Groq",
            gender="Woman",
            target_gender="Man",
            location="San Francisco, CA",
            linkedin_url=f"https://www.linkedin.com/in/alice-groq-{test_uid}",
            linkedin_handle=f"alice-groq-{test_uid}",
            instagram_url=f"https://www.instagram.com/alice_groq_{test_uid}",
            instagram_handle=f"alice_groq_{test_uid}",
            consent_status="consented",
            is_synthetic=True,
            simulation_eligible=True
        )
        p_b = Participant(
            id=p_b_id,
            name="Bob Groq",
            gender="Man",
            target_gender="Woman",
            location="San Francisco, CA",
            linkedin_url=f"https://www.linkedin.com/in/bob-groq-{test_uid}",
            linkedin_handle=f"bob-groq-{test_uid}",
            instagram_url=f"https://www.instagram.com/bob_groq_{test_uid}",
            instagram_handle=f"bob_groq_{test_uid}",
            consent_status="consented",
            is_synthetic=True,
            simulation_eligible=True
        )
        db.add(p_a)
        db.add(p_b)

        prof_a = AnalyzedProfile(
            participant_id=p_a.id,
            summary="Alice is an outdoor photographer and software engineer.",
            career_interests=["Software Engineering"],
            demonstrated_hobbies=["Rock Climbing", "Photography"],
            stated_interests=["Travel", "Hiking"],
            communication_preferences=["Thoughtful", "Curious"]
        )
        prof_b = AnalyzedProfile(
            participant_id=p_b.id,
            summary="Bob is a product manager and mountain biker.",
            career_interests=["Product Management"],
            demonstrated_hobbies=["Mountain Biking", "Cooking"],
            stated_interests=["Camping", "Philosophy"],
            communication_preferences=["Engaging", "Warm"]
        )
        db.add(prof_a)
        db.add(prof_b)
        db.commit()

        captured_user_prompts = []

        def mock_groq_generate(system_prompt, user_prompt, temperature=0.7, max_tokens=1500, response_schema=None):
            captured_user_prompts.append(user_prompt)
            if "Agent Dating Turn" in system_prompt or "Turn" in user_prompt:
                turn_num = len([p for p in captured_user_prompts if "Turn" in p])
                speaker = "Alice" if turn_num % 2 != 0 else "Bob"
                return MockGroqCompletion(
                    content=json.dumps({
                        "internal_thought": f"{speaker} thinking at turn {turn_num}.",
                        "decision_summary": f"{speaker} responding thoughtfully.",
                        "decision_factors": ["Active listening", "Shared outdoor interests"],
                        "message": f"Hello, this is {speaker} speaking on turn {turn_num}!",
                        "question_asked": "What inspired your passion for the outdoors?",
                        "interest_referenced": "Outdoors"
                    }),
                    prompt_tokens=150,
                    completion_tokens=60
                )
            elif "evaluating" in system_prompt.lower() or "evaluation" in system_prompt.lower():
                return MockGroqCompletion(
                    content=json.dumps({
                        "chemistry_score": 8.5,
                        "communication_comfort": 9.0,
                        "shared_values_alignment": 8.0,
                        "would_date_again": True,
                        "evaluation_rationale": "High intellectual rapport and warm flow.",
                        "perceived_green_flags": ["Active listener", "Shared outdoor passion"],
                        "perceived_red_flags": [],
                        "unanswered_questions": ["Favorite weekend destination"]
                    }),
                    prompt_tokens=220,
                    completion_tokens=80
                )
            return MockGroqCompletion(content=json.dumps({"status": "ok"}))

        # Configure Groq provider
        monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
        monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_valid_key")

        with patch("groq.Groq") as MockGroq:
            client_instance = MagicMock()
            client_instance.chat.completions.create.side_effect = lambda **kwargs: mock_groq_generate(
                system_prompt=kwargs["messages"][0]["content"],
                user_prompt=kwargs["messages"][1]["content"],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1500),
                response_schema=kwargs.get("response_format")
            )
            MockGroq.return_value = client_instance

            # Create and execute 4-turn session
            session = DatingSession(
                id=sess_id,
                participant_a_id=p_a.id,
                participant_b_id=p_b.id,
                status="initialized",
                run_id="test-groq-run"
            )
            db.add(session)
            db.commit()

            res = execute_dating_session(db, session.id, max_turns=4)

            assert res.status == "completed"
            assert res.outcome_status == "second_date_agreed"
            assert res.total_turns == 4
            assert res.current_turn == 4
            assert res.total_tokens_used > 0
            assert res.approx_cost_usd > 0

            # Verify persisted messages
            messages = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session.id
            ).order_by(ConversationMessage.turn_number.asc()).all()

            assert len(messages) == 4

            # Verify alternating turns
            assert messages[0].turn_number == 1
            assert messages[0].sender_agent_role == "Agent A"
            assert messages[0].sender_participant_id == p_a.id
            assert "Alice speaking on turn 1" in messages[0].content

            assert messages[1].turn_number == 2
            assert messages[1].sender_agent_role == "Agent B"
            assert messages[1].sender_participant_id == p_b.id
            assert "Bob speaking on turn 2" in messages[1].content

            assert messages[2].turn_number == 3
            assert messages[2].sender_agent_role == "Agent A"
            assert messages[2].sender_participant_id == p_a.id

            assert messages[3].turn_number == 4
            assert messages[3].sender_agent_role == "Agent B"
            assert messages[3].sender_participant_id == p_b.id

            # Verify context preservation: Turn 2's prompt included Turn 1's message
            turn_prompts = [p for p in captured_user_prompts if "Turn" in p]
            assert "Alice speaking on turn 1" in turn_prompts[1]
            # Turn 3's prompt included Turn 1 and Turn 2
            assert "Bob speaking on turn 2" in turn_prompts[2]

            # Verify persisted evaluations
            evals = db.query(AgentEvaluation).filter(
                AgentEvaluation.session_id == session.id
            ).all()
            assert len(evals) == 2
            eval_a = next(e for e in evals if e.evaluator_participant_id == p_a.id)
            eval_b = next(e for e in evals if e.evaluator_participant_id == p_b.id)
            assert eval_a.target_participant_id == p_b.id
            assert eval_b.target_participant_id == p_a.id
            assert eval_a.would_date_again is True
            assert eval_b.would_date_again is True

            # Calculate and verify rankings
            rankings = calculate_rankings_for_participant(db, p_a.id, run_id="test-groq-run")
            assert len(rankings) > 0
            bob_ranking = next((r for r in rankings if r.target_participant_id == p_b.id), None)
            assert bob_ranking is not None
            assert bob_ranking.individual_score > 0
            assert bob_ranking.reciprocal_score > 0
    finally:
        db.close()
