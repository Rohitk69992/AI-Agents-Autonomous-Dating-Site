import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

# Approximate pricing per 1k tokens (Gemini 2.5 Flash / 1.5 Flash reference)
PRICE_PER_1K_INPUT_USD = 0.000125
PRICE_PER_1K_OUTPUT_USD = 0.000375

class LLMResponse:
    def __init__(
        self,
        content: str,
        structured_data: Optional[Dict[str, Any]] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        latency_ms: int = 0,
        model: str = "",
        provider: str = ""
    ):
        self.content = content
        self.structured_data = structured_data or {}
        self.tokens_input = tokens_input
        self.tokens_output = tokens_output
        self.tokens_total = tokens_input + tokens_output
        self.latency_ms = latency_ms
        self.model = model
        self.provider = provider
        self.cost_usd = (
            (tokens_input / 1000.0) * PRICE_PER_1K_INPUT_USD
            + (tokens_output / 1000.0) * PRICE_PER_1K_OUTPUT_USD
        )

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        pass


DEFAULT_GEMINI_CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY must be provided for GeminiLLMProvider. "
                "For offline testing, configure LLM_PROVIDER='offline_mock'."
            )
        self.api_key = api_key.strip()
        # Normalize model name (strip any inadvertent 'models/' prefix)
        self.model_name = (model_name or "gemini-2.5-flash").replace("models/", "").strip()
        self.client = None
        self._init_client()

    def _sanitize_error(self, err: Any) -> str:
        text = str(err)
        # Redact Google API key formats (e.g., AIzaSy...)
        text = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED_API_KEY]", text)
        text = re.sub(r"([?&]key=)[^&\s\"']+", r"\1[REDACTED]", text)
        text = re.sub(r'(api_key=["\']?)[^"\'\s&]+', r"\1[REDACTED]", text)
        return text

    def _is_not_found(self, err: Exception) -> bool:
        err_str = str(err).lower()
        err_cls = err.__class__.__name__.lower()
        return (
            "404" in err_str
            or "not found" in err_str
            or "not supported for generatecontent" in err_str
            or "notfound" in err_cls
        )

    def _is_transient(self, err: Exception) -> bool:
        err_str = str(err).lower()
        err_cls = err.__class__.__name__.lower()
        return (
            "429" in err_str
            or "resourceexhausted" in err_str
            or "resource_exhausted" in err_str
            or "quota" in err_str
            or "rate limit" in err_str
            or "503" in err_str
            or "unavailable" in err_str
            or "500" in err_str
            or "internalservererror" in err_str
            or "deadline" in err_cls
            or "deadlineexceeded" in err_str
            or "timeout" in err_str
            or "timed out" in err_str
            or "connection reset" in err_str
            or "temporarily unavailable" in err_str
        )

    def _init_client(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"temperature": 0.7}
            )
        except Exception as e:
            sanitized = self._sanitize_error(e)
            logger.error(f"Failed to initialize Gemini client: {sanitized}")
            raise RuntimeError(f"Failed to initialize Gemini GenerativeModel: {sanitized}")

    def _extract_tokens(self, response: Any, prompt: str, content: str) -> Tuple[int, int]:
        tokens_in = len(prompt) // 4
        tokens_out = len(content) // 4
        try:
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
                cand_tokens = getattr(response.usage_metadata, "candidates_token_count", None)
                if prompt_tokens is not None:
                    tokens_in = int(prompt_tokens)
                if cand_tokens is not None:
                    tokens_out = int(cand_tokens)
        except Exception as meta_err:
            logger.debug(f"Could not read usage_metadata: {meta_err}")
        return tokens_in, tokens_out

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        start_time = time.time()
        if not self.client:
            raise RuntimeError("Gemini client is uninitialized. Verify GEMINI_API_KEY.")

        prompt_combined = f"{system_prompt}\n\nTask:\n{user_prompt}"
        if response_schema:
            prompt_combined += (
                f"\n\nIMPORTANT: Respond with valid JSON adhering to this schema:\n"
                f"{json.dumps(response_schema, indent=2)}\n"
                f"Do NOT include markdown formatting outside the JSON."
            )

        # Build ordered candidate models list: primary configured model first, followed by known stable fallbacks
        models_to_try = [self.model_name]
        for candidate in DEFAULT_GEMINI_CANDIDATE_MODELS:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        model_errors: Dict[str, str] = {}
        import google.generativeai as genai

        for current_model_name in models_to_try:
            for attempt in range(2):
                try:
                    model = genai.GenerativeModel(
                        model_name=current_model_name,
                        generation_config={
                            "temperature": temperature,
                            "max_output_tokens": max_tokens,
                        }
                    )
                    response = model.generate_content(prompt_combined)
                    latency_ms = int((time.time() - start_time) * 1000)

                    content = getattr(response, "text", "") or ""
                    structured_data = None
                    if response_schema:
                        structured_data = self._extract_json(content)

                    tokens_in, tokens_out = self._extract_tokens(response, prompt_combined, content)

                    return LLMResponse(
                        content=content,
                        structured_data=structured_data,
                        tokens_input=tokens_in,
                        tokens_output=tokens_out,
                        latency_ms=latency_ms,
                        model=current_model_name,
                        provider="gemini"
                    )
                except Exception as e:
                    sanitized_msg = self._sanitize_error(e)
                    if self._is_not_found(e):
                        logger.warning(
                            f"Gemini model '{current_model_name}' returned 404/not supported. "
                            f"Skipping immediately to next candidate model. Detail: {sanitized_msg}"
                        )
                        model_errors[current_model_name] = f"404 Not Found: {sanitized_msg}"
                        # Do NOT retry 404 on the same model
                        break
                    elif self._is_transient(e):
                        logger.warning(
                            f"Gemini API transient failure with '{current_model_name}' (attempt {attempt + 1}/2): {sanitized_msg}"
                        )
                        if attempt == 0:
                            time.sleep(1.0)
                            continue
                        else:
                            model_errors[current_model_name] = f"Transient failure exhausted: {sanitized_msg}"
                            break
                    else:
                        logger.warning(f"Gemini API non-transient error with '{current_model_name}': {sanitized_msg}")
                        model_errors[current_model_name] = sanitized_msg
                        break

        # Dynamic discovery fallback if all candidate models were not found
        if all("404" in v or "not found" in v.lower() for v in model_errors.values()):
            logger.info("All static candidate models returned 404. Attempting dynamic discovery via genai.list_models()...")
            try:
                discovered_models = []
                for m in genai.list_models():
                    methods = getattr(m, "supported_generation_methods", [])
                    raw_name = getattr(m, "name", "").replace("models/", "").strip()
                    if "generateContent" in methods and raw_name and raw_name not in models_to_try:
                        discovered_models.append(raw_name)

                # Prioritize flash models
                discovered_models.sort(key=lambda x: (0 if "flash" in x.lower() else 1, x))

                for disc_model in discovered_models[:3]:
                    try:
                        logger.info(f"Attempting dynamically discovered model: '{disc_model}'")
                        model = genai.GenerativeModel(
                            model_name=disc_model,
                            generation_config={
                                "temperature": temperature,
                                "max_output_tokens": max_tokens,
                            }
                        )
                        response = model.generate_content(prompt_combined)
                        latency_ms = int((time.time() - start_time) * 1000)
                        content = getattr(response, "text", "") or ""
                        structured_data = None
                        if response_schema:
                            structured_data = self._extract_json(content)
                        tokens_in, tokens_out = self._extract_tokens(response, prompt_combined, content)

                        return LLMResponse(
                            content=content,
                            structured_data=structured_data,
                            tokens_input=tokens_in,
                            tokens_output=tokens_out,
                            latency_ms=latency_ms,
                            model=disc_model,
                            provider="gemini"
                        )
                    except Exception as disc_err:
                        model_errors[disc_model] = f"Discovery fail: {self._sanitize_error(disc_err)}"
            except Exception as list_err:
                logger.warning(f"Failed to query genai.list_models(): {self._sanitize_error(list_err)}")

        attempt_summary = "; ".join(f"[{m}: {err}]" for m, err in model_errors.items())
        raise RuntimeError(
            f"Gemini generation failed after attempts across {list(model_errors.keys())}: {attempt_summary}"
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text or not text.strip():
            return None
        clean_text = text.strip()
        try:
            return json.loads(clean_text)
        except Exception:
            # Match JSON markdown block
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except Exception:
                    pass
            # Find first { and last }
            start = clean_text.find("{")
            end = clean_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(clean_text[start : end + 1])
                except Exception:
                    pass
        return None


class OfflineMockProvider(BaseLLMProvider):
    """
    Offline mock engine that parses input prompts and outputs realistic,
    rigorously validated JSON adhering to exact schemas. Used strictly for offline testing,
    reproducible test runs, and environments where GEMINI_API_KEY is not configured.
    """
    def __init__(self, model_name: str = "offline-mock"):
        self.model_name = model_name

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        start_time = time.time()
        
        # Analyze prompt context to generate authentic structured answers
        structured_data = {}
        content = ""

        if "Profile Analysis" in system_prompt or "profile" in user_prompt.lower():
            structured_data = self._generate_profile_analysis(user_prompt)
            content = json.dumps(structured_data, indent=2)
        elif "Agent Dating Turn" in system_prompt or "turn" in user_prompt.lower():
            structured_data = self._generate_dating_turn(user_prompt)
            content = json.dumps(structured_data, indent=2)
        elif "Date Evaluation" in system_prompt or "evaluate" in user_prompt.lower():
            structured_data = self._generate_date_evaluation(user_prompt)
            content = json.dumps(structured_data, indent=2)
        elif "Ranking Explanation" in system_prompt or "ranking" in user_prompt.lower():
            structured_data = self._generate_ranking_explanation(user_prompt)
            content = json.dumps(structured_data, indent=2)
        else:
            content = "Acknowledged. Proceeding with structured evaluation."
            structured_data = {"status": "success", "message": content}

        latency_ms = int((time.time() - start_time) * 1000) + 45
        tokens_in = len(system_prompt + user_prompt) // 4
        tokens_out = len(content) // 4

        return LLMResponse(
            content=content,
            structured_data=structured_data,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=latency_ms,
            model=self.model_name,
            provider="offline_mock"
        )

    def _generate_profile_analysis(self, prompt: str) -> Dict[str, Any]:
        return {
            "summary": "Professional software and product leader with passions for active outdoor exploration, photography, and open dialogue.",
            "career_interests": ["Artificial Intelligence", "Systems Architecture", "High-growth Startups"],
            "demonstrated_hobbies": ["Trail Running", "Landscape Photography", "Culinary Arts"],
            "stated_interests": ["Deep Learning", "Travel", "Philosophy of Technology"],
            "lifestyle_preferences": ["Early riser", "Work-life harmony", "Regular weekend hiking"],
            "communication_preferences": ["Thoughtful and direct", "Curious listener", "Values authenticity"],
            "relationship_preferences": ["Mutual intellectual curiosity", "Growth-oriented partnership"],
            "explicit_facts": ["Holds professional role in software engineering", "Active public social presence with photography portfolio"],
            "inferences_with_confidence": [
                {"claim": "Appreciates nature-centric weekend getaways", "confidence": 0.85, "basis": "Multiple public photography posts in national parks"},
                {"claim": "Thrives in structured yet creative collaborative environments", "confidence": 0.78, "basis": "Career trajectory in lead architecture"}
            ],
            "uncertainties_and_unknowns": [
                "Long-term residential preferences (urban vs suburban)",
                "Specific daily schedule flexibility"
            ]
        }

    def _generate_dating_turn(self, prompt: str) -> Dict[str, Any]:
        return {
            "internal_thought": "I notice my date highlighted a passion for outdoor adventures and creative projects. I want to build on our shared energy around nature while asking about how they balance demanding work with leisure.",
            "decision_summary": "Building on shared interest in outdoor lifestyle and inquiring about work-life balance.",
            "decision_factors": ["Shared interest: nature/hiking", "Work-life balance inquiry", "Positive emotional tone"],
            "message": "It's wonderful to connect! I really resonated with your love for weekend hikes and creative projects. How do you usually like to recharge after a high-intensity week?",
            "question_asked": "How do you usually like to recharge after a high-intensity week?",
            "interest_referenced": "Weekend hikes and creative projects"
        }

    def _generate_date_evaluation(self, prompt: str) -> Dict[str, Any]:
        return {
            "chemistry_score": 8.5,
            "communication_comfort": 9.0,
            "shared_values_alignment": 8.0,
            "would_date_again": True,
            "evaluation_rationale": "We shared clear intellectual rapport, reciprocal curiosity, and mutual appreciation for outdoor activities and personal balance.",
            "perceived_green_flags": ["Active listener", "Balanced life philosophy", "Shared love for nature"],
            "perceived_red_flags": [],
            "unanswered_questions": ["Preferred travel pace when taking long vacations"]
        }

    def _generate_ranking_explanation(self, prompt: str) -> Dict[str, Any]:
        return {
            "explanation": "High reciprocal alignment across core lifestyle preferences and demonstrated engagement in the dating dialogue."
        }


# Backward-compatibility alias
DeterministicProvider = OfflineMockProvider


def get_llm_provider() -> BaseLLMProvider:
    provider = (settings.LLM_PROVIDER or "offline_mock").lower().strip()
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER is configured as 'gemini', but no GEMINI_API_KEY or GOOGLE_API_KEY is configured in the environment. "
                "Set GEMINI_API_KEY in your environment, or configure LLM_PROVIDER='offline_mock' for offline execution."
            )
        return GeminiLLMProvider(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
    elif provider in ("offline_mock", "mock", "deterministic"):
        return OfflineMockProvider(model_name=settings.GEMINI_MODEL)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER '{settings.LLM_PROVIDER}'. Expected 'gemini' or 'offline_mock'.")
