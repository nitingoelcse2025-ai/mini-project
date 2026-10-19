# 🌾 KisanMitra AI – A Multilingual Intelligent Farming Assistant

> **A college mini-project MVP empowering Indian farmers with simple, practical, and multilingual agricultural guidance.**

---

## 📖 1. Project Overview

**KisanMitra AI** is a lightweight, mobile-first web application designed for farmers with low technical literacy. It bridges the gap between modern artificial intelligence and grassroots agriculture by delivering simple, actionable, and safe advice in **Hindi (हिंदी)** and **English**.

### Key Objectives:
- **Low-literacy Friendly:** Large touch-targets, intuitive icons, high-contrast layouts, and simple conversational explanations without confusing jargon.
- **Bilingual by Design:** Instantly toggle between Hindi and English; language preference persists across sessions and drives AI prompts.
- **Safety First:** Emphasizes eco-friendly, organic remedies first and always includes protective warnings for agrochemicals.
- **Transparent AI & Offline Awareness:** Responses clearly indicate whether they originated from live AI (`"source": "ai"`) or a local fallback (`"source": "fallback"`), displaying a prominent amber banner during offline demonstrations.
- **Plant Diagnostic Integrity:** Never serves canned or fake diagnoses. If Gemini Vision is unavailable, the plant-check API cleanly returns HTTP 503.

---

## 🛠️ 2. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite | High-performance SPA with instant HMR and client-side image downscaling |
| **Styling** | Tailwind CSS | Custom green & earthy palette, mobile-first design |
| **Routing & Icons** | react-router-dom, Lucide React | Intuitive navigation and accessible iconography |
| **HTTP Client** | Axios | Seamless backend communication and standardized error handling |
| **Localization** | Custom React i18n Context | Full Hindi & English dictionaries (`en.json`, `hi.json`) with complete parity |
| **Voice Input** | Browser Web Speech API | Hands-free Hindi (`hi-IN`) and English (`en-IN`) voice queries |
| **Backend** | Python 3.12, Flask, Flask-CORS | Modular REST API with structured blueprints and per-IP rate limiting |
| **Database** | SQLite3 | Local storage of live AI query history and diagnostics |
| **AI Engine** | Google Gemini API (`google-genai`) | Configurable primary and fallback models for text and multimodal vision |
| **Weather** | Open-Meteo API | Free, keyless meteorological forecasts and geocoding |
| **Testing** | Pytest | Comprehensive integration tests with mocked AI and external APIs |

---

## 📁 3. Folder Structure

```
kisanmitra-ai/
├── .gitignore
├── README.md
├── backend/
│   ├── app.py                      # Flask main entry, CORS, blueprints, error handlers, seeds
│   ├── database.py                 # SQLite init, schema, CRUD helper functions
│   ├── limiter.py                  # In-memory sliding window rate limiter (~20 req/min)
│   ├── requirements.txt            # Python production dependencies
│   ├── requirements-dev.txt        # Python development & testing dependencies (pytest)
│   ├── .env                        # Local environment variables (ignored in Git)
│   ├── .env.example                # Example configuration template
│   ├── routes/
│   │   ├── chat.py                 # POST /api/chat (conversational assistant)
│   │   ├── crop.py                 # POST /api/crop-advice (sowing & schedule)
│   │   ├── weather.py              # GET/POST /api/weather (forecast & tips, save=true flag)
│   │   ├── plant.py                # POST /api/plant-check (multimodal vision, 503 on failure)
│   │   └── history.py              # GET/DELETE /api/history (database records, clamped limit)
│   ├── services/
│   │   ├── gemini_service.py       # Configurable Gemini models, quota detection, and fallbacks
│   │   └── weather_service.py      # Open-Meteo geocoding & forecast parser
│   └── tests/
│       ├── __init__.py             # Test package marker
│       └── test_api.py             # 13 integration test cases with mock services
└── frontend/
    ├── index.html                  # HTML entry point with Mukta/Outfit fonts & valid SVG favicon
    ├── vite.config.js              # Vite bundler config with /api proxy
    ├── tailwind.config.js          # Custom theme configuration
    ├── postcss.config.js           # PostCSS Tailwind plugins
    ├── package.json                # Frontend dependencies and scripts
    └── src/
        ├── main.jsx                # React root mount with Router & i18n
        ├── App.jsx                 # Layout and page route definitions
        ├── index.css               # Base Tailwind directives and custom scrollbar
        ├── api/
        │   └── client.js           # Axios client instance with bilingual error handling
        ├── context/
        │   └── LanguageContext.jsx # Persistent language state & translation lookup
        ├── i18n/
        │   ├── en.json             # English translation strings
        │   └── hi.json             # Hindi translation strings
        ├── components/
        │   ├── Navbar.jsx          # Header with brand, nav links & lang toggle
        │   ├── LanguageToggle.jsx  # One-click Hindi/English switcher
        │   ├── ChatBubble.jsx      # Formatted bubbles with offline fallback banner & copy button
        │   ├── WeatherCard.jsx     # Current weather metrics, 5-day forecast & AI tip
        │   ├── CropForm.jsx        # Indian crops dropdown and localized season selector
        │   ├── PlantUpload.jsx     # Canvas client-side downscaling (1600px) & 5MB validation
        │   ├── Loader.jsx          # Farming-themed spinner component
        │   └── ErrorMessage.jsx    # User-friendly error alert with retry
        └── pages/
            ├── Home.jsx            # Hero banner, 5 feature cards & helpline
            ├── CropAdvice.jsx      # Crop advisory planning tool with fallback alert
            ├── Weather.jsx         # Live weather forecast, localStorage recall & save=true
            ├── Chat.jsx            # Conversational assistant with localStorage & voice input
            ├── PlantCheck.jsx      # Plant photo health diagnosis (503 handling)
            └── History.jsx         # Query records with filtering, clamped limits & delete
```

---

## ⚙️ 4. Environment Variables

Configure your backend settings in `backend/.env` (reference `backend/.env.example`):

| Variable | Default Value | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(None)* | Google Gemini API Key from Google AI Studio |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Primary Gemini model for text and vision generation |
| `GEMINI_FALLBACK_MODELS` | *(Empty)* | Optional comma-separated models tried if primary fails |
| `HOST` | `127.0.0.1` | Backend bind host address |
| `PORT` | `5000` | Backend port number |
| `FLASK_DEBUG` | `false` | Enable or disable Flask debug mode |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed CORS origins (comma-separated) |

---

## ⚡ 5. Installation & Local Setup

### Prerequisites
- **Python** (version 3.10+)
- **Node.js** (version 18+ or 20+) and **npm**

### Step A: Backend Setup
1. Open a terminal and navigate to `backend`:
   ```bash
   cd backend
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   - On Windows:
     ```powershell
     python -m venv venv
     venv\Scripts\activate
     ```
   - On Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install production dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment configuration and edit `.env`:
   ```bash
   cp .env.example .env
   ```
5. Start the backend:
   ```bash
   python app.py
   ```
   Backend will run on **`http://127.0.0.1:5000`**.

---

### Step B: Frontend Setup
1. Open a second terminal window and navigate to `frontend`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser at **`http://localhost:5173`**.

---

## 🧪 6. Running Tests

The backend includes a comprehensive pytest test suite covering validation, error handling, rate limiting, and database interactions with mocked Gemini and Open-Meteo services.

1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Install test dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Run the test suite:
   ```bash
   python -m pytest -v
   ```

To verify the frontend production build:
```bash
cd frontend
npm run build
```

---

## 📡 7. API Reference

| Endpoint | Method | Rate Limit | Description |
|---|---|---|---|
| `/api/health` | `GET` | Unlimited | Health check & service status |
| `/api/crop-advice` | `POST` | 20 / min | Crop advisory guidelines. Returns `source: "ai" \| "fallback"`. |
| `/api/weather` | `GET`/`POST` | 20 / min | Live weather & farming tip. Saves to history **only** when `save=true`. |
| `/api/chat` | `POST` | 20 / min | Multi-turn agricultural chatbot. Returns `source: "ai" \| "fallback"`. |
| `/api/plant-check` | `POST` | 20 / min | Multimodal plant photo diagnosis. Returns 503 if AI fails (never fakes diagnosis). |
| `/api/history` | `GET` | Unlimited | View stored queries (`limit` clamped between 1 and 200). |
| `/api/history/<id>`| `DELETE` | Unlimited | Delete a past query record (returns 404 if not found). |

---

## 🔒 8. Security & Resilience Features

- **Rate Limiting:** Protects `/api/chat`, `/api/crop-advice`, `/api/plant-check`, and `/api/weather` at ~20 requests/minute per client IP (HTTP 429).
- **Quota & Rate Limit Detection:** Detects HTTP 429 / RESOURCE_EXHAUSTED from Gemini and cleanly responds with HTTP 429 and a friendly bilingual message.
- **Client-Side Image Optimization:** Images uploaded to Plant Check are automatically downscaled to a maximum of 1600px on the longest side using HTML5 Canvas (JPEG 0.85 quality) before upload, reducing network payload while preserving diagnostic details.
- **No Leaked Exceptions:** Server-side exceptions are logged to the console while returning clean, friendly error messages to clients.
- **Offline Transparency:** Chat, Crop Advice, and Weather responses clearly state their source. When offline fallback answers are shown, an amber alert banner informs the user that live AI is unavailable.

---

## 🎯 9. Viva & Demonstration Walkthrough

1. **Ask AI Chat Assistant & Voice Input:**
   - Click the microphone icon next to the chat input to speak your farming query in Hindi or English.
   - Click "Clear" to wipe the chat; notice that refreshing the page retains chat history across sessions (`kisanmitra_chat`).
2. **Crop Advisory:**
   - Select crop, season, and soil type to generate a structured 5-part guide.
3. **Live Weather & Local Storage:**
   - Search for a city (e.g. `Jaipur`, `Nagpur`) or click **"Use My Location"**.
   - Notice that reloading the page restores your last searched city without duplicate history entries (`save=true` only for manual searches).
4. **Plant Photo Check & Integrity:**
   - Upload any leaf photo (supports camera and file upload, auto-downscaled to 1600px).
   - If a valid Gemini API key is configured, an AI diagnostic report is returned.
   - If the API key is removed or invalid, the app returns a clear HTTP 503 error rather than a misleading canned diagnosis.
5. **Query History:**
   - Review saved queries categorized by Crop, Weather, Chat, and Plant Scans.
   - Fallback responses are never saved to history. Click the trash icon to delete records with interactive confirmation.
6. **Bilingual Toggle:**
   - Click the "हिंदी" / "English" toggle in the navigation bar to instantly switch languages across all 6 pages.

---

## 📄 License & Credits
Built for academic presentation and college mini-project evaluation. Powered by Google Gemini and Open-Meteo.
