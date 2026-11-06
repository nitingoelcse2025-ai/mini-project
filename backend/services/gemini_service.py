"""
Gemini AI Service for KisanMitra AI.
Handles all interactions with Google Gemini API for:
1. Multilingual Agriculture Chatbot
2. Crop Advisory & Farming Schedule
3. Weather-based Farming Tips
4. Plant Disease & Health Diagnosis (Gemini Vision)

Includes reliable fallback responses for college presentations and offline testing.
"""

import os
import sys
import json
import re
import time
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dotenv import load_dotenv

# Load environment variables from explicit absolute path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, ".env"))

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
_last_gemini_error_reason = "service_unavailable"

# Failed models cooldown cache: {model_name: timestamp_of_failure}
_failed_models: Dict[str, float] = {}
FAILED_MODEL_COOLDOWN_SECONDS: float = 300.0  # 5 minutes
TOTAL_REQUEST_BUDGET_SECONDS: float = 25.0


class GeminiRateLimitError(Exception):
    """Raised when Gemini API quota or rate limit is exhausted (429 / RESOURCE_EXHAUSTED)."""
    pass


def is_model_in_cooldown(model_name: str) -> bool:
    """Checks whether a model is currently in 5-minute failure cooldown."""
    failed_at = _failed_models.get(model_name)
    if not failed_at:
        return False
    if time.time() - failed_at < FAILED_MODEL_COOLDOWN_SECONDS:
        return True
    _failed_models.pop(model_name, None)
    return False


def mark_model_failed(model_name: str) -> None:
    """Records failure timestamp for a model to skip it for the next 5 minutes."""
    _failed_models[model_name] = time.time()
    logger.info(f"Model '{model_name}' marked as failed; skipping for the next 5 minutes.")


def clear_failed_models() -> None:
    """Clears failed models cooldown cache (useful for testing and resets)."""
    _failed_models.clear()


def should_cooldown_model(reason_type: str, clean_desc: str, exc: Exception) -> bool:
    """Determines whether an error qualifies for a 5-minute cooldown (404/not-found, invalid key, timeout)."""
    if reason_type in ("model not found", "invalid key"):
        return True
    err_text = (clean_desc + " " + str(exc)).upper()
    if any(k in err_text for k in ("TIMEOUT", "TIMED OUT", "DEADLINE", "504", "404", "NOT_FOUND", "NOT FOUND", "NO LONGER AVAILABLE")):
        return True
    return False


def get_model_candidates() -> List[str]:
    """
    Returns candidate models in priority order.
    Configured via GEMINI_MODEL (default: gemini-2.5-flash) and optional GEMINI_FALLBACK_MODELS.
    Respects GEMINI_FALLBACK_MODELS exactly as set, including an empty value.
    Does NOT append extra forced models.
    """
    primary = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    fallback_env = os.getenv("GEMINI_FALLBACK_MODELS")
    if fallback_env is not None:
        fallbacks = [m.strip() for m in fallback_env.split(",") if m.strip()]
    else:
        fallbacks = []
    candidates = [primary] + [m for m in fallbacks if m != primary]
    return candidates


def is_rate_limit_error(e: Exception) -> bool:
    """Checks if an exception is related to rate limiting or quota exhaustion (429 / RESOURCE_EXHAUSTED)."""
    err_str = str(e).upper()
    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str or "RATE_LIMIT" in err_str:
        return True
    if hasattr(e, "code") and getattr(e, "code") == 429:
        return True
    return False


def categorize_gemini_error(e: Exception) -> Tuple[str, str]:
    """
    Categorizes a Gemini API exception into (reason_type, clean_description).
    Reason types: 'quota', 'model not found', 'invalid key', 'network', 'service unavailable', 'unknown'.
    Guarantees that the secret API key is NEVER exposed in logs.
    """
    raw_str = str(e)
    # Strip any potential API key from error string
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key and api_key in raw_str:
        raw_str = raw_str.replace(api_key, "[REDACTED]")

    err_upper = raw_str.upper()

    if "429" in err_upper or "RESOURCE_EXHAUSTED" in err_upper or "QUOTA" in err_upper or "RATE_LIMIT" in err_upper:
        return "quota", "Quota or rate limit exhausted"
    elif "503" in err_upper or "UNAVAILABLE" in err_upper or "HIGH DEMAND" in err_upper:
        return "service unavailable", "Service temporarily experiencing high demand"
    elif "504" in err_upper or "DEADLINE" in err_upper or "TIMEOUT" in err_upper or "TIMED OUT" in err_upper:
        return "network", "Deadline exceeded / network timeout"
    elif "404" in err_upper or "NOT_FOUND" in err_upper or "NOT FOUND" in err_upper or "NO LONGER AVAILABLE" in err_upper:
        return "model not found", "Model not found or unsupported"
    elif "400" in err_upper or "401" in err_upper or "403" in err_upper or "API_KEY" in err_upper or "UNAUTHENTICATED" in err_upper or "PERMISSION" in err_upper:
        return "invalid key", "Invalid API key or unauthorized access"
    elif "CONNECTION" in err_upper or "NETWORK" in err_upper or "DNS" in err_upper:
        return "network", "Network connection or DNS error"
    else:
        return "unknown", raw_str[:120]


def get_gemini_client():
    """Initializes and returns the Gemini client if API key is present."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        from google.genai import types
        http_options = types.HttpOptions(
            timeout=12000,
            retry_options=types.HttpRetryOptions(attempts=1)
        )
        return genai.Client(api_key=api_key, http_options=http_options)
    except Exception as e:
        reason_type, desc = categorize_gemini_error(e)
        sys.stderr.write(f"[Gemini Error] Model: None | Reason: {reason_type} ({desc})\n")
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None


def build_generate_content_config(
    system_instruction: Optional[str] = None,
    temperature: float = 0.4,
    max_output_tokens: Optional[int] = None,
    enable_thinking: bool = True,
) -> Any:
    """Builds GenerateContentConfig with optional token limits and LOW thinking config."""
    from google.genai import types

    config_kwargs: Dict[str, Any] = {"temperature": temperature}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if max_output_tokens is not None:
        config_kwargs["max_output_tokens"] = max_output_tokens

    if enable_thinking:
        try:
            if hasattr(types, "ThinkingConfig"):
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="LOW")
        except Exception as te:
            logger.debug(f"ThinkingConfig init skipped: {te}")

    return types.GenerateContentConfig(**config_kwargs)


def call_gemini_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> Optional[str]:
    """Helper to invoke Gemini text generation across candidate models with timeout budget and cooldown."""
    global _last_gemini_error_reason
    client = get_gemini_client()
    if not client:
        _last_gemini_error_reason = "key_missing"
        sys.stderr.write("[Gemini Error] Model: None | Reason: invalid key (missing or placeholder)\n")
        logger.warning("Gemini text call skipped: API key missing or invalid.")
        return None

    contents = prompt
    config = build_generate_content_config(
        system_instruction=system_instruction,
        temperature=0.4,
        max_output_tokens=max_output_tokens,
        enable_thinking=True,
    )

    models = get_model_candidates()
    rate_limit_hit = False
    start_time = time.time()

    for model_name in models:
        # Check total time budget across all models
        if time.time() - start_time >= TOTAL_REQUEST_BUDGET_SECONDS:
            logger.warning(
                f"Total time budget ({TOTAL_REQUEST_BUDGET_SECONDS}s) exceeded. Stopping candidate model attempts."
            )
            _last_gemini_error_reason = "service_unavailable"
            break

        # Skip models currently in 5-minute cooldown
        if is_model_in_cooldown(model_name):
            logger.info(f"Skipping model '{model_name}' due to recent failure (5-minute cooldown active).")
            continue

        call_start = time.time()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            elapsed = time.time() - call_start
            logger.info(f"Gemini call succeeded: model='{model_name}', elapsed={elapsed:.2f}s")
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            # If rejected, retry once without thinking_config if it was used and budget allows
            if (
                getattr(config, "thinking_config", None) is not None
                and (time.time() - start_time < TOTAL_REQUEST_BUDGET_SECONDS)
            ):
                logger.info(f"Retrying model '{model_name}' without thinking_config after error: {e}")
                retry_start = time.time()
                try:
                    fallback_config = config.model_copy(deep=True) if hasattr(config, "model_copy") else config
                    fallback_config.thinking_config = None
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=fallback_config,
                    )
                    retry_elapsed = time.time() - retry_start
                    logger.info(f"Gemini call succeeded (retry without thinking): model='{model_name}', elapsed={retry_elapsed:.2f}s")
                    if response and response.text:
                        return response.text.strip()
                except Exception as retry_err:
                    e = retry_err

            elapsed = time.time() - call_start
            reason_type, clean_desc = categorize_gemini_error(e)
            sys.stderr.write(f"[Gemini Error] Model: {model_name} | Elapsed: {elapsed:.2f}s | Reason: {reason_type} ({clean_desc})\n")
            logger.warning(f"Gemini call failed: model='{model_name}', elapsed={elapsed:.2f}s, reason={reason_type} - {clean_desc}")

            if should_cooldown_model(reason_type, clean_desc, e):
                mark_model_failed(model_name)

            if reason_type == "quota":
                rate_limit_hit = True
                _last_gemini_error_reason = "rate_limit"
            elif reason_type == "invalid key":
                _last_gemini_error_reason = "key_missing"
            elif reason_type == "model not found":
                _last_gemini_error_reason = "model_not_found"
            else:
                _last_gemini_error_reason = "service_unavailable"
            continue

    if rate_limit_hit:
        raise GeminiRateLimitError("Gemini API rate limit or quota exceeded (RESOURCE_EXHAUSTED / 429).")

    if time.time() - start_time >= TOTAL_REQUEST_BUDGET_SECONDS:
        _last_gemini_error_reason = "service_unavailable"

    return None


def call_gemini_vision(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    system_instruction: Optional[str] = None,
    max_output_tokens: Optional[int] = 1000,
) -> Optional[str]:
    """Helper to invoke Gemini vision multimodal analysis."""
    global _last_gemini_error_reason
    client = get_gemini_client()
    if not client:
        _last_gemini_error_reason = "key_missing"
        sys.stderr.write("[Gemini Error] Model: None | Reason: invalid key (missing or placeholder)\n")
        return None

    from google.genai import types

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    contents = [prompt, image_part]

    config = build_generate_content_config(
        system_instruction=system_instruction,
        temperature=0.3,
        max_output_tokens=max_output_tokens,
        enable_thinking=True,
    )

    models = get_model_candidates()
    rate_limit_hit = False
    start_time = time.time()

    for model_name in models:
        if time.time() - start_time >= TOTAL_REQUEST_BUDGET_SECONDS:
            logger.warning(f"Total time budget ({TOTAL_REQUEST_BUDGET_SECONDS}s) exceeded in vision call.")
            _last_gemini_error_reason = "service_unavailable"
            break

        if is_model_in_cooldown(model_name):
            logger.info(f"Skipping vision model '{model_name}' due to 5-minute cooldown.")
            continue

        call_start = time.time()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            elapsed = time.time() - call_start
            logger.info(f"Gemini vision call succeeded: model='{model_name}', elapsed={elapsed:.2f}s")
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            if (
                getattr(config, "thinking_config", None) is not None
                and (time.time() - start_time < TOTAL_REQUEST_BUDGET_SECONDS)
            ):
                logger.info(f"Retrying vision on model '{model_name}' without thinking_config after error: {e}")
                retry_start = time.time()
                try:
                    fallback_config = config.model_copy(deep=True) if hasattr(config, "model_copy") else config
                    fallback_config.thinking_config = None
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=fallback_config,
                    )
                    retry_elapsed = time.time() - retry_start
                    logger.info(f"Gemini vision call succeeded (retry without thinking): model='{model_name}', elapsed={retry_elapsed:.2f}s")
                    if response and response.text:
                        return response.text.strip()
                except Exception as retry_err:
                    e = retry_err

            elapsed = time.time() - call_start
            reason_type, clean_desc = categorize_gemini_error(e)
            sys.stderr.write(f"[Gemini Error] Model: {model_name} | Elapsed: {elapsed:.2f}s | Reason: {reason_type} ({clean_desc})\n")
            logger.warning(f"Error calling vision on '{model_name}': elapsed={elapsed:.2f}s, reason={reason_type} - {clean_desc}")

            if should_cooldown_model(reason_type, clean_desc, e):
                mark_model_failed(model_name)

            if reason_type == "quota":
                rate_limit_hit = True
                _last_gemini_error_reason = "rate_limit"
            else:
                _last_gemini_error_reason = "service_unavailable"
            continue

    if rate_limit_hit:
        raise GeminiRateLimitError("Gemini API rate limit or quota exceeded (RESOURCE_EXHAUSTED / 429).")

    return None


def check_ai_status() -> Dict[str, Any]:
    """
    Performs a live connectivity test using a minimal Gemini call ('Say OK').
    NEVER logs or returns the API key. Does not save to database.
    Returns:
    {
        "key_loaded": bool,
        "model": str,
        "live_test": "ok" | "failed",
        "error": str | None
    }
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    primary_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            "key_loaded": False,
            "model": primary_model,
            "live_test": "failed",
            "error": "API key not configured"
        }

    client = get_gemini_client()
    if not client:
        return {
            "key_loaded": True,
            "model": primary_model,
            "live_test": "failed",
            "error": "Failed to initialize Gemini client"
        }

    models = get_model_candidates()
    last_err_desc = "API call failed"
    for m in models:
        if is_model_in_cooldown(m):
            logger.info(f"AI status check skipping model '{m}' (5-minute cooldown active).")
            continue

        call_start = time.time()
        try:
            res = client.models.generate_content(
                model=m,
                contents="Say OK",
            )
            elapsed = time.time() - call_start
            logger.info(f"AI status test succeeded: model='{m}', elapsed={elapsed:.2f}s")
            if res and res.text:
                return {
                    "key_loaded": True,
                    "model": m,
                    "live_test": "ok",
                    "error": None
                }
        except Exception as e:
            elapsed = time.time() - call_start
            reason_type, clean_desc = categorize_gemini_error(e)
            sys.stderr.write(f"[Gemini Error] Model: {m} | Elapsed: {elapsed:.2f}s | Reason: {reason_type} ({clean_desc})\n")
            logger.warning(f"AI status live test failed for model '{m}': elapsed={elapsed:.2f}s, reason={reason_type} - {clean_desc}")
            if should_cooldown_model(reason_type, clean_desc, e):
                mark_model_failed(m)
            last_err_desc = clean_desc
            continue

    return {
        "key_loaded": True,
        "model": primary_model,
        "live_test": "failed",
        "error": last_err_desc
    }


# =====================================================================
# 1. Ask AI Chat Assistant
# =====================================================================

def generate_chat_reply(
    message: Optional[Union[str, List[Dict[str, str]]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    language: str = "hi",
    messages: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, str]:
    """
    Answers farmer queries strictly on agriculture topics with safety checks.
    Supports either (message, history) or legacy (messages) list.
    Returns {"text": str, "source": "ai" | "fallback", "reason": Optional[str]}.
    """
    lang_name = "Hindi (हिंदी)" if language == "hi" else "English"

    # If messages list was passed as first positional argument
    if isinstance(message, list):
        messages = message
        message = None

    # Normalize messages list
    formatted_messages: List[Dict[str, str]] = []
    if history:
        for item in history[-6:]:
            if isinstance(item, dict) and item.get("content"):
                formatted_messages.append({
                    "role": item.get("role", "user"),
                    "content": item.get("content", "").strip(),
                })
    elif messages:
        for item in messages[-6:]:
            if isinstance(item, dict) and item.get("content"):
                formatted_messages.append({
                    "role": item.get("role", "user"),
                    "content": item.get("content", "").strip(),
                })

    if message and isinstance(message, str) and message.strip():
        formatted_messages.append({"role": "user", "content": message.strip()})

    system_prompt = (
        f"You are KisanMitra AI, a friendly and empathetic agriculture assistant for Indian farmers. "
        f"Answer ONLY farming and agriculture-related questions (crops, soil, weather, irrigation, fertilizers, pests, livestock, government schemes like PM-KISAN, seeds). "
        f"If the question is not related to farming or agriculture, politely refuse and remind the user that you are an agricultural assistant. "
        f"Use very simple words, short sentences, and practical bullet points. "
        f"Reply in {lang_name}. "
        f"If you are unsure about something, clearly say so and advise visiting the local Krishi Vigyan Kendra (KVK) or Agriculture Extension Officer. "
        f"Never give dangerous pesticide dosage advice without a prominent safety warning (wear gloves/mask, follow packet directions)."
    )

    history_lines = []
    for msg in formatted_messages[-7:]:
        role = "Farmer" if msg.get("role") == "user" else "KisanMitra"
        text = msg.get("content", "").strip()
        if text:
            history_lines.append(f"{role}: {text}")

    full_prompt = (
        "Here is the recent conversation between the farmer and you:\n"
        + "\n".join(history_lines)
        + "\n\nPlease reply to the farmer's latest query now:"
    )

    # Chat max_output_tokens set to approx 600
    result = call_gemini_text(full_prompt, system_instruction=system_prompt, max_output_tokens=600)
    if result:
        return {"text": result, "source": "ai"}

    # Determine fallback reason
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        fallback_reason = "key_missing"
    else:
        fallback_reason = _last_gemini_error_reason or "service_unavailable"

    # Smart domain fallback when API key is unavailable or quota exhausted
    latest_msg = ""
    for m in reversed(formatted_messages):
        if m.get("role") == "user":
            latest_msg = m.get("content", "").lower().strip()
            break

    # Non-farming refusal check in fallback mode
    non_farming_keywords = [
        "code", "python", "javascript", "movie", "film", "song", "cricket", "football",
        "actor", "actress", "politics", "president", "prime minister", "game", "recipe for cake",
        "कोडिंग", "गाना", "फिल्म", "क्रिकेट", "राजनीति"
    ]
    if any(k in latest_msg for k in non_farming_keywords):
        if language == "hi":
            return {
                "text": "🙏 क्षमा करें, मैं केवल खेती-बाड़ी, फसल, मौसम, खाद और कृषि संबंधित सवालों में ही सहायता कर सकता हूँ। कृपया खेती से जुड़ा कोई सवाल पूछें।",
                "source": "fallback",
                "reason": fallback_reason,
            }
        else:
            return {
                "text": "🙏 I am sorry, I am KisanMitra AI and I only answer farming and agriculture-related questions (crops, soil, weather, pests, fertilizers). Please ask a farming query.",
                "source": "fallback",
                "reason": fallback_reason,
            }
    if language == "hi":
        if any(w in latest_msg for w in ["खाद", "यूरिया", "dap", "उर्वरक"]):
            fallback_text = (
                "🌱 **खाद व उर्वरक सलाह (KisanMitra)**:\n\n"
                "• बुवाई के समय संतुलित मात्रा में NPK या DAP का प्रयोग करें।\n"
                "• रासायनिक खाद के साथ प्रति एकड़ 4-5 ट्रॉली अच्छी तरह सड़ी गोबर की खाद अवश्य मिलाएं।\n"
                "• खड़ी फसल में यूरिया की टॉप ड्रेसिंग नमी होने पर ही करें।\n"
                "⚠️ *सलाह:* कीटनाशक या रासायनिक खाद छिड़कते समय मास्क और दस्ताने अवश्य पहनें।"
            )
        elif any(w in latest_msg for w in ["पानी", "सिंचाई", "irrigation"]):
            fallback_text = (
                "💧 **सिंचाई प्रबंधन सलाह**:\n\n"
                "• हमेशा सुबह या शाम के समय ही सिंचाई करें ताकि पानी का वाष्पीकरण कम हो।\n"
                "• यदि बारिश की संभावना हो तो सिंचाई 2-3 दिन टालें।\n"
                "• टपक (ड्रिप) या फव्वारा सिंचाई से पानी और बिजली दोनों की भारी बचत होती है।"
            )
        else:
            fallback_text = (
                "नमस्ते किसान भाई! 🙏 मैं किसानमित्र एआई हूँ।\n\n"
                "• आपके सवाल का जवाब तैयार किया जा रहा है।\n"
                "• कृपया अपनी फसल का नाम, मिट्टी का प्रकार और बुवाई का समय विस्तार से बताएं।\n"
                "• किसी भी गंभीर समस्या के लिए अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
            )
    else:
        fallback_text = (
            "Hello Farmer friend! 🙏 I am KisanMitra AI, your farming assistant.\n\n"
            "• For best crop growth, ensure proper soil testing and balanced NPK fertilizer application.\n"
            "• Irrigate during early morning or evening hours to conserve moisture.\n"
            "• For specific pests or severe diseases, consult your local Krishi Vigyan Kendra (KVK) officer.\n"
            "⚠️ *Safety Warning:* Always wear protective gloves and a face mask when spraying crop chemicals."
        )

    return {"text": fallback_text, "source": "fallback", "reason": fallback_reason}


# =====================================================================
# 2. Crop Advice
# =====================================================================

def generate_crop_advice(crop: str, season: str, soil: str = "", question: str = "", language: str = "hi") -> Dict[str, str]:
    """
    Generates structured crop advisory: sowing, irrigation, care, problems, and fertilizers.
    Returns {"text": str, "source": "ai" | "fallback"}.
    """
    lang_name = "Hindi (हिंदी)" if language == "hi" else "English"

    prompt = (
        f"Provide comprehensive, practical farming guidance for the following crop:\n"
        f"- Crop Name: {crop}\n"
        f"- Season: {season}\n"
        f"- Soil Type: {soil or 'Not specified'}\n"
        f"- Farmer's specific question: {question or 'General complete crop guide'}\n\n"
        f"Strict format requirements:\n"
        f"1. Language: Answer purely in {lang_name}.\n"
        f"2. Use simple, easily understandable words for Indian rural farmers.\n"
        f"3. Format into these 5 clear headings with bullet points:\n"
        f"   - 📅 1. बुवाई का समय और तरीका (When to Sow & Seed Treatment)\n"
        f"   - 💧 2. सिंचाई का समय और चक्र (Irrigation Schedule)\n"
        f"   - 🌿 3. बुनियादी देखभाल और निराई-गुड़ाई (Basic Care & Weeding)\n"
        f"   - 🐛 4. सामान्य रोग, कीट और बचाव (Common Pests & Disease Care)\n"
        f"   - 🧪 5. खाद और उर्वरक प्रबंधन (Fertilizer & Compost Tips)\n"
        f"4. Include a safety note for spraying pesticides."
    )

    system_prompt = (
        f"You are KisanMitra AI, an expert agricultural scientist advising Indian farmers in {lang_name}. "
        f"Keep the tone encouraging, warm and practical."
    )

    # Crop advice max_output_tokens set to approx 900
    result = call_gemini_text(prompt, system_instruction=system_prompt, max_output_tokens=900)
    if result:
        return {"text": result, "source": "ai"}

    # Offline / Fallback advisory
    if language == "hi":
        fallback_text = f"""### 🌾 {crop} की संपूर्ण कृषि सलाह ({season} मौसम)

📅 **1. बुवाई का समय और बीज उपचार:**
• {season} मौसम में तापमान अनुकूल होने पर बुवाई करें।
• प्रमाणित बीजों का ही चयन करें और प्रति किलो बीज को 2-3 ग्राम फफूंदनाशक (थीरम/बाविस्टिन) से उपचारित करें।
• कतार से कतार और पौधे से पौधे की उचित दूरी बनाए रखें।

💧 **2. सिंचाई का समय और चक्र:**
• पहली सिंचाई बुवाई के 20-25 दिन बाद (क्रांतिक अवस्था पर) करें।
• फूल आने और फल/दाने बनते समय खेत में पर्याप्त नमी बनाए रखना अति आवश्यक है।
• खेत में जलभराव न होने दें, उचित जल निकासी रखें।

🌿 **3. बुनियादी देखभाल और निराई-गुड़ाई:**
• बुवाई के 25-30 दिन बाद पहली निराई-गुड़ाई करके खरपतवार निकालें।
• मिट्टी चढ़ाने से पौधों की जड़ें मजबूत होती हैं।

🐛 **4. सामान्य कीट व रोग नियंत्रण:**
• माहू (एफिड्स) या रस चूसक कीटों के लिए 5% नीम तेल (नीम का काढ़ा) का छिड़काव करें।
• दीमक की रोकथाम के लिए बुवाई से पहले खेत की गहरी जुताई करें।

🧪 **5. खाद और उर्वरक प्रबंधन:**
• खेत की तैयारी के समय 4-5 ट्रॉली सड़ी गोबर खाद डालें।
• मिट्टी परीक्षण के आधार पर यूरिया, डीएपी (DAP) व पोटाश का संतुलित प्रयोग करें।

⚠️ *सुरक्षा चेतावनी:* कीटनाशक का छिड़काव करते समय हमेशा मुंह पर मास्क व हाथों में दस्ताने पहनें और हवा की दिशा में ही स्प्रे करें।"""
    else:
        fallback_text = f"""### 🌾 Complete Farming Guide for {crop} ({season} Season)

📅 **1. When to Sow & Seed Treatment:**
• Sow at the recommended optimal temperature for {season} season.
• Use certified, high-yield disease-resistant seeds. Treat seeds with Trichoderma (5g/kg) or Carbendazim (2g/kg) before sowing.
• Maintain proper row-to-row and plant-to-plant spacing.

💧 **2. Irrigation Schedule:**
• Apply first irrigation 20-25 days after sowing (critical crown root stage).
• Maintain uniform moisture during flowering and grain/fruit filling stages.
• Avoid waterlogging; ensure proper field drainage.

🌿 **3. Basic Crop Care & Weeding:**
• Carry out manual weeding or hoeing 25-30 days after sowing.
• Proper earthing-up provides strength to roots and improves yield.

🐛 **4. Common Pests & Disease Management:**
• For sucking pests (aphids, jassids), spray 5% Neem seed kernel extract (NSKE) or Neem oil.
• Watch for fungal leaf spots; apply bio-fungicide at early symptoms.

🧪 **5. Fertilizer & Nutrient Management:**
• Incorporate 4-5 trolleys of well-decomposed FYM (Farmyard Manure) during land preparation.
• Apply balanced N:P:K according to soil testing recommendations.

⚠️ *Safety Advisory:* Always wear face masks and protective gloves when applying agricultural sprays and keep away from children."""

    return {"text": fallback_text, "source": "fallback"}


# =====================================================================
# 3. Weather-based Farming Tips
# =====================================================================

def generate_weather_tip(weather_data: Dict[str, Any], language: str = "hi") -> Dict[str, str]:
    """
    Analyzes weather indicators (temp, humidity, rain chance, wind) and produces actionable farming advisory.
    Returns {"text": str, "source": "ai" | "fallback"}.
    """
    lang_name = "Hindi (हिंदी)" if language == "hi" else "English"

    current = weather_data.get("current", {})
    temp = current.get("temperature", "--")
    humidity = current.get("humidity", "--")
    wind = current.get("wind_speed", "--")
    rain_prob = current.get("rain_probability", 0)
    city = weather_data.get("location_name", "your area")

    prompt = (
        f"Based on the following weather conditions for {city}:\n"
        f"- Current Temperature: {temp}°C\n"
        f"- Relative Humidity: {humidity}%\n"
        f"- Wind Speed: {wind} km/h\n"
        f"- Probability of Rain: {rain_prob}%\n\n"
        f"Provide a concise, practical farming advisory in {lang_name} (2 to 4 bullet points).\n"
        f"Cover:\n"
        f"1. Irrigation advice (e.g., should they water today or pause due to rain?)\n"
        f"2. Spraying precautions (windy or rain risk?)\n"
        f"3. Sowing/harvesting or protection advice for standing crops.\n"
        f"Keep the language very simple and direct for farmers."
    )

    system_prompt = f"You are KisanMitra AI, an expert agro-meteorologist advising Indian farmers in {lang_name}."

    # Weather tip max_output_tokens set to approx 500
    result = call_gemini_text(prompt, system_instruction=system_prompt, max_output_tokens=500)
    if result:
        return {"text": result, "source": "ai"}

    # Weather heuristic fallback
    rain_val = int(rain_prob) if str(rain_prob).isdigit() else 0
    wind_val = float(wind) if str(wind).replace(".", "", 1).isdigit() else 10.0

    if language == "hi":
        if rain_val > 40:
            fallback_text = (
                "🌧️ **मौसम आधारित कृषि सलाह (KisanMitra):**\n\n"
                "• **सिंचाई रोकें:** बारिश की संभावना अधिक है, इसलिए आज खेतों में सिंचाई न करें। इससे पानी और लागत दोनों की बचत होगी।\n"
                "• **छिड़काव न करें:** बारिश के कारण किसी भी कीटनाशक या खाद का पर्णीय छिड़काव न करें, दवा धुल सकती है।\n"
                "• **जल निकासी:** खेत में जलभराव की स्थिति से बचने के लिए मेड़ और नालियां साफ रखें।"
            )
        elif wind_val > 20:
            fallback_text = (
                "💨 **मौसम आधारित कृषि सलाह (KisanMitra):**\n\n"
                "• **छिड़काव स्थगित रखें:** हवा की गति तेज होने से कीटनाशक का बहाव लक्ष्य से भटक सकता है, छिड़काव शांत मौसम में करें।\n"
                "• **लंबी फसलों को सहारा दें:** मक्का, गन्ना व केले जैसी फसलों की मेड़बंदी मजबूत करें।\n"
                "• **सिंचाई:** हल्की सिंचाई शाम के समय करें।"
            )
        else:
            fallback_text = (
                "☀️ **मौसम आधारित कृषि सलाह (KisanMitra):**\n\n"
                "• **सिंचाई के लिए अनुकूल दिन:** मौसम साफ है, आवश्यकतानुसार फसलों में हल्की सिंचाई कर सकते हैं।\n"
                "• **दवा व खाद का छिड़काव:** सुबह 8-11 बजे या शाम 4 बजे के बाद कीटनाशक/उर्वरक छिड़काव के लिए मौसम उपयुक्त है।\n"
                "• **निराई-गुड़ाई:** धूप खिली रहने से खरपतवार सूखने के लिए खेत की निराई करें।"
            )
    else:
        if rain_val > 40:
            fallback_text = (
                "🌧️ **Weather-Based Agro Advisory (KisanMitra):**\n\n"
                "• **Postpone Irrigation:** High chance of rain. Pause irrigation today to save water and prevent soil saturation.\n"
                "• **Avoid Chemical Spraying:** Do not spray pesticides or foliar fertilizers as rain will wash them away.\n"
                "• **Drainage:** Keep field channels and bunds clear to prevent stagnant waterlogging."
            )
        elif wind_val > 20:
            fallback_text = (
                "💨 **Weather-Based Agro Advisory (KisanMitra):**\n\n"
                "• **Pause Spray Operations:** High wind speed causes chemical drift; avoid pesticide spraying today.\n"
                "• **Support Tall Crops:** Check lodging protection for tall crops like sugarcane, maize, and banana.\n"
                "• **Moisture Check:** Moderate soil drying; water crops during calm evening hours."
            )
        else:
            fallback_text = (
                "☀️ **Weather-Based Agro Advisory (KisanMitra):**\n\n"
                "• **Favorable Conditions:** Clear weather. Proceed with normal irrigation and inter-cultivation activities.\n"
                "• **Spraying Window:** Weather is suitable for bio-pesticide or micronutrient sprays during early morning or late afternoon.\n"
                "• **Weed Removal:** Good sunlight allows pulled weeds to desiccate quickly."
            )

    return {"text": fallback_text, "source": "fallback"}


# =====================================================================
# 4. Plant Health / Disease Diagnosis (Vision)
# =====================================================================

def generate_plant_diagnosis(
    image_bytes: bytes,
    mime_type: str,
    language: str = "hi",
    crop: str = "",
) -> Dict[str, str]:
    """
    Analyzes crop image using Gemini Vision for disease, pest, or nutrient deficiencies.
    Returns probable problem, symptoms, treatment (organic + chemical), and prevention.
    Returns {"text": str, "source": "ai"} on success or {"text": "", "source": "fallback"} on failure.
    NEVER returns a fake diagnostic report.
    """
    lang_name = "Hindi (हिंदी)" if language == "hi" else "English"

    crop_context = f"\nThe farmer says this is a {crop} plant." if crop else ""

    prompt = (
        f"You are KisanMitra AI, an agricultural plant pathologist. "
        f"Carefully examine this plant / leaf / crop photo and provide a structured diagnosis in {lang_name}.{crop_context}\n\n"
        f"Structure your response exactly with these 4 sections:\n"
        f"1. 🔍 **संभावित समस्या / Probable Problem:** (Identify the disease, pest attack, or nutrient deficiency)\n"
        f"2. 📋 **पहचान और लक्षण / Symptoms Explained:** (Describe what visual symptoms appear on leaves/stem)\n"
        f"3. 💊 **उपचार और समाधान / Recommended Treatment:**\n"
        f"   - **जैविक / Organic:** (Natural solutions like neem oil, cow urine concoction, bio-fungicides)\n"
        f"   - **रासायनिक / Chemical:** (Common approved agrochemicals with dosage caution)\n"
        f"4. 🛡️ **रोकथाम के उपाय / Prevention Tips:** (Cultural practices, crop rotation, soil care)\n\n"
        f"Always conclude with this exact note:\n"
        f"⚠️ **अस्वीकरण (Disclaimer):** यह एक एआई सुझाव है, कोई पक्का लैब निदान नहीं। गंभीर समस्या होने पर अपने नजदीकी कृषि विशेषज्ञ या कृषि विज्ञान केंद्र (KVK) से सलाह लें।"
    )

    system_prompt = (
        f"You are KisanMitra AI plant health expert. "
        f"Explain clearly and simply in {lang_name} so any farmer can understand and take safe action."
    )

    result = call_gemini_vision(image_bytes, mime_type, prompt, system_instruction=system_prompt, max_output_tokens=1000)
    if result:
        return {"text": result, "source": "ai"}

    # NEVER return a fake diagnosis if AI vision fails
    return {"text": "", "source": "fallback"}
