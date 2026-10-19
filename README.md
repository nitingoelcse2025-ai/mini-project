# 🌾 KisanMitra AI – A Multilingual Intelligent Farming Assistant

> **A college mini-project MVP empowering Indian farmers with simple, practical, and multilingual agricultural guidance.**

---

## 📖 1. Project Overview

**KisanMitra AI** is a lightweight, mobile-first web application designed for farmers with low technical literacy. It bridges the gap between modern artificial intelligence and grassroots agriculture by delivering simple, actionable, and safe advice in **Hindi (हिंदी)** and **English**.

### Key Objectives:
- **Low-literacy Friendly:** Large touch-targets, intuitive icons, high-contrast layouts, and simple conversational explanations without confusing jargon.
- **Bilingual by Design:** Instantly toggle between Hindi and English; language preference persists across sessions and drives AI prompts.
- **Safety First:** Emphasizes eco-friendly, organic remedies first and always includes protective warnings for agrochemicals.
- **Zero-Setup Resilience:** Powered by Google Gemini and Open-Meteo with smart local fallbacks and sample seed data for viva and offline evaluations.

---

## 🛠️ 2. Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite | High-performance SPA with instant HMR |
| **Styling** | Tailwind CSS | Custom green & earthy palette, mobile-first design |
| **Routing & Icons** | react-router-dom, Lucide React | Intuitive navigation and accessible iconography |
| **HTTP Client** | Axios | Seamless backend communication and error handling |
| **Localization** | Custom React i18n Context | Lightweight Hindi & English dictionaries (`en.json`, `hi.json`) |
| **Backend** | Python 3.12, Flask, Flask-CORS | Modular REST API with structured blueprints |
| **Database** | SQLite3 | Local storage of query history and diagnostics |
| **AI Engine** | Google Gemini API (`google-genai`) | Text and Vision reasoning for agronomy |
| **Weather** | Open-Meteo API | Free, keyless meteorological forecasts and geocoding |

---

## 📁 3. Folder Structure

```
kisanmitra-ai/
├── .gitignore
├── README.md
├── backend/
│   ├── app.py                      # Flask main entry, CORS, blueprints, seeds
│   ├── database.py                 # SQLite init, schema, CRUD helper functions
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Local environment variables (ignored in Git)
│   ├── .env.example                # Example configuration template
│   ├── routes/
│   │   ├── chat.py                 # POST /api/chat (conversational assistant)
│   │   ├── crop.py                 # POST /api/crop-advice (sowing & schedule)
│   │   ├── weather.py              # GET/POST /api/weather (forecast & tips)
│   │   ├── plant.py                # POST /api/plant-check (multimodal vision)
│   │   └── history.py              # GET/DELETE /api/history (database records)
│   └── services/
│       ├── gemini_service.py       # Gemini API client, prompts, and fallbacks
│       └── weather_service.py      # Open-Meteo geocoding & forecast parser
└── frontend/
    ├── index.html                  # HTML entry point with Mukta & Outfit fonts
    ├── vite.config.js              # Vite bundler config with /api proxy
    ├── tailwind.config.js          # Custom theme configuration
    ├── postcss.config.js           # PostCSS Tailwind plugins
    ├── package.json                # Frontend dependencies and scripts
    └── src/
        ├── main.jsx                # React root mount with Router & i18n
        ├── App.jsx                 # Layout and page route definitions
        ├── index.css               # Base Tailwind directives and custom scrollbar
        ├── api/
        │   └── client.js           # Axios client instance with error handling
        ├── context/
        │   └── LanguageContext.jsx # Persistent language state & translation lookup
        ├── i18n/
        │   ├── en.json             # English translation strings
        │   └── hi.json             # Hindi translation strings
        ├── components/
        │   ├── Navbar.jsx          # Header with logo, nav links & lang toggle
        │   ├── LanguageToggle.jsx  # One-click Hindi/English switcher
        │   ├── ChatBubble.jsx      # Formatted user and assistant chat bubbles
        │   ├── WeatherCard.jsx     # Current weather stats, forecast & AI tip
        │   ├── CropForm.jsx        # Indian crops dropdown and season picker
        │   ├── PlantUpload.jsx     # Camera/photo upload with 5MB validation
        │   ├── Loader.jsx          # Farming-themed spinner component
        │   └── ErrorMessage.jsx    # User-friendly error alert with retry
        └── pages/
            ├── Home.jsx            # Hero banner, 5 feature cards & helpline
            ├── CropAdvice.jsx      # Crop advisory planning tool
            ├── Weather.jsx         # Live weather forecast and daily tips
            ├── Chat.jsx            # Agriculture conversational assistant
            ├── PlantCheck.jsx      # Plant photo health diagnosis
            └── History.jsx         # Query records with filtering & delete
```

---

## ⚡ 4. Installation & Local Setup

### Prerequisites
- **Python** (version 3.10+ recommended)
- **Node.js** (version 18+ or 20+) and **npm**

### Step A: Backend Setup
1. Open a terminal and navigate to the `backend` directory:
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
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your Gemini API key in `backend/.env`:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   PORT=5000
   FLASK_ENV=development
   ```
   > *Note:* If you do not have an API key right now, the backend includes built-in domain fallbacks for presentation and testing.
5. Start the Flask server:
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

## 📡 5. API Reference

| Endpoint | Method | Description | Sample Request / Query |
|---|---|---|---|
| `/api/health` | `GET` | Health check & service status | None |
| `/api/crop-advice` | `POST` | Crop advisory guidelines | `{"crop": "Wheat", "season": "Rabi", "language": "hi"}` |
| `/api/weather` | `GET`/`POST` | Live weather & farming tip | `?city=Jaipur&language=hi` or `?lat=26.9&lon=75.8` |
| `/api/chat` | `POST` | Multi-turn agricultural chatbot | `{"messages": [{"role":"user","content":"धान में कीट नियंत्रण"}], "language":"hi"}` |
| `/api/plant-check` | `POST` | Vision disease diagnosis | Multipart form (`image` file, `crop`, `language`) |
| `/api/history` | `GET` | View stored queries | `?type=all` or `?type=crop` (limit 100) |
| `/api/history/<id>`| `DELETE` | Delete a past query record | URL param `id` |

---

## 🎯 6. Sample Queries for Viva & Demonstration

Use these pre-tested prompts to showcase the app during evaluation:

### 1. Crop Advisory
- **Crop:** Wheat (गेहूं) | **Season:** Rabi (रबी) | **Question:** "पहली सिंचाई कब करें और खाद की मात्रा क्या रखें?"
- **Crop:** Rice (धान) | **Season:** Kharif (खरीफ) | **Question:** "खरपतवार नियंत्रण और यूरिया डालने का सही तरीका"

### 2. Live Weather
- Search for Indian agricultural regions: `Jaipur`, `Nagpur`, `Pune`, `Patna`, `Ludhiana`, or click **"Use My Location"**.
- Notice the AI-generated **"Smart Farming Tip for Today"** reflecting rain probability and wind speed.

### 3. Ask AI Chat Assistant
- *"धान की फसल में पत्ता लपेटक कीट का जैविक उपचार बताएं"*
- *"आलू की फसल में पाले से बचाव के क्या उपाय हैं?"*
- Non-farming test (verifies strict guardrail refusal): *"What is the capital of France?"* -> AI politely reminds it only answers farming questions.

### 4. Plant Photo Check
- Upload any sample plant leaf image (`.jpg` or `.png`).
- Watch the AI produce: 1) Probable Problem, 2) Symptoms, 3) Organic & Chemical Treatment, 4) Prevention Tips.

---

## 🚀 7. Future Scope

1. **Voice Input & Regional Dialects:** Web Speech API integration to allow farmers to speak questions in Bhojpuri, Marwari, Punjabi, or Kannada.
2. **Offline Progressive Web App (PWA):** Caching basic crop calendars and pest guides for intermittent rural internet connectivity.
3. **Mandi Prices Integration (e-NAM):** Real-time daily market price comparison across nearby agricultural markets.
4. **Soil Health Card Integration:** Uploading soil test reports to calculate precise NPK fertilizer requirements down to kilogram precision.
5. **Government Subsidy Alert System:** Push notifications for PM-KISAN, crop insurance (PMFBY), and solar pump subsidy deadlines.

---

## 📄 License & Credits
Built for academic presentation and college mini-project evaluation. Powered by Google Gemini and Open-Meteo.
