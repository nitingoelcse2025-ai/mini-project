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
import json
import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


class GeminiRateLimitError(Exception):
    """Raised when Gemini API quota or rate limit is exhausted (429 / RESOURCE_EXHAUSTED)."""
    pass


def get_model_candidates() -> List[str]:
    """
    Returns candidate models in priority order.
    Configured via GEMINI_MODEL (default: gemini-2.5-flash) and optional GEMINI_FALLBACK_MODELS.
    """
    primary = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    fallback_str = os.getenv("GEMINI_FALLBACK_MODELS", "").strip()
    fallbacks = [m.strip() for m in fallback_str.split(",") if m.strip()]
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


def get_gemini_client():
    """Initializes and returns the Gemini client if API key is present."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None


def call_gemini_text(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """Helper to invoke Gemini text generation across candidate models."""
    client = get_gemini_client()
    if not client:
        return None

    from google.genai import types

    contents = prompt
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    config.temperature = 0.4

    models = get_model_candidates()
    rate_limit_hit = False

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            if response and response.text:
                logger.info(f"Gemini text answered successfully using model '{model_name}'")
                return response.text.strip()
        except Exception as e:
            if is_rate_limit_error(e):
                rate_limit_hit = True
                logger.warning(f"Rate limit / quota exhausted on model '{model_name}': {e}")
            else:
                logger.warning(f"Error calling {model_name}: {e}")
            continue

    if rate_limit_hit:
        raise GeminiRateLimitError("Gemini API rate limit or quota exceeded (RESOURCE_EXHAUSTED / 429).")

    return None


def call_gemini_vision(image_bytes: bytes, mime_type: str, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """Helper to invoke Gemini vision multimodal analysis."""
    client = get_gemini_client()
    if not client:
        return None

    from google.genai import types

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    contents = [prompt, image_part]

    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    config.temperature = 0.3

    models = get_model_candidates()
    rate_limit_hit = False

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            if response and response.text:
                logger.info(f"Gemini vision answered successfully using model '{model_name}'")
                return response.text.strip()
        except Exception as e:
            if is_rate_limit_error(e):
                rate_limit_hit = True
                logger.warning(f"Rate limit / quota exhausted on vision model '{model_name}': {e}")
            else:
                logger.warning(f"Error calling vision on {model_name}: {e}")
            continue

    if rate_limit_hit:
        raise GeminiRateLimitError("Gemini API rate limit or quota exceeded (RESOURCE_EXHAUSTED / 429).")

    return None


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
    Returns {"text": str, "source": "ai" | "fallback"}.
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

    result = call_gemini_text(full_prompt, system_instruction=system_prompt)
    if result:
        return {"text": result, "source": "ai"}

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
            }
        else:
            return {
                "text": "🙏 I am sorry, I am KisanMitra AI and I only answer farming and agriculture-related questions (crops, soil, weather, pests, fertilizers). Please ask a farming query.",
                "source": "fallback",
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

    return {"text": fallback_text, "source": "fallback"}


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

    result = call_gemini_text(prompt, system_instruction=system_prompt)
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

    result = call_gemini_text(prompt, system_instruction=system_prompt)
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

    result = call_gemini_vision(image_bytes, mime_type, prompt, system_instruction=system_prompt)
    if result:
        return {"text": result, "source": "ai"}

    # NEVER return a fake diagnosis if AI vision fails
    return {"text": "", "source": "fallback"}
