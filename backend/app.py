"""
KisanMitra AI Backend
Main Flask application entry point.
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import DB and blueprints
from database import init_db, get_queries, save_query
from routes.chat import chat_bp
from routes.crop import crop_bp
from routes.weather import weather_bp
from routes.plant import plant_bp
from routes.history import history_bp


def seed_sample_data():
    """Populates initial representative sample queries if database is empty for demo purposes."""
    try:
        existing = get_queries(limit=1)
        if not existing:
            logger.info("Database empty. Seeding initial demo sample queries...")
            save_query(
                query_type="crop",
                question="गेहूं (रबी मौसम), दोमट मिट्टी - बुवाई व सिंचाई सलाह",
                response="""### 🌾 गेहूं की संपूर्ण कृषि सलाह (रबी मौसम)
📅 **1. बुवाई का समय और बीज उपचार:**
• 1 से 20 नवंबर तक का समय सर्वोत्तम है। प्रमाणित HD-2967 या DBW-187 बीज 40 किग्रा/एकड़ की दर से उपयोग करें।
• थीरम (2.5 ग्राम/किग्रा) से बीज उपचारित करें।

💧 **2. सिंचाई का समय:**
• पहली सिंचाई 21 दिन पर मुकुट जड़ (CRI) अवस्था में अति आवश्यक है।
• इसके बाद कल्ले फूटते, गांठ बनते और बालियां निकलते समय सिंचाई करें।

🧪 **3. खाद और उर्वरक:**
• बुवाई के समय 1 बोरी DAP + आधा बोरा पोटाश। पहली व दूसरी सिंचाई पर आधा-आधा बोरा यूरिया दें।""",
                language="hi",
            )
            save_query(
                query_type="weather",
                question="Weather for Jaipur, Rajasthan",
                response="Temp: 32°C, Condition: साफ आसमान (Clear sky). Tip: ☀️ मौसम साफ और शुष्क है। सिंचाई और कीटनाशक छिड़काव के लिए अनुकूल समय है।",
                language="hi",
            )
            save_query(
                query_type="chat",
                question="धान की फसल में तना छेदक कीट लगा है, क्या करें?",
                response="""🌾 **धान में तना छेदक (Stem Borer) नियंत्रण:**
• **पहचान:** पौधे की बीच की गोफ सूख जाती है जिसे 'मृत गोफ' (Dead Heart) कहते हैं।
• **जैविक समाधान:** प्रति एकड़ 4-5 फेरोमोन ट्रैप लगाएं और ट्राइकोग्रामा परजीवी कार्ड 20,000 प्रति एकड़ छोड़ें।
• **रासायनिक उपचार:** गंभीर प्रकोप में कारटैप हाइड्रोक्लोराइड 4% G (7-8 किग्रा प्रति एकड़) रेत में मिलाकर खेत में डालें।
⚠️ *सावधानी:* छिड़काव या दवा डालते समय मास्क व दस्ताने अवश्य पहनें।""",
                language="hi",
            )
            save_query(
                query_type="plant",
                question="Plant Check: tomato_leaf_early_blight.jpg (Tomato)",
                response="""🔍 **संभावित समस्या:** टमाटर में अगेती झुलसा (Early Blight - Alternaria solani)
📋 **लक्षण:** निचली पत्तियों पर संकेंद्रित छल्लों (Target spot) वाले भूरे-काले धब्बे।
💊 **उपचार:**
• जैविक: 5% नीम तेल स्प्रे करें।
• रासायनिक: मैंकोजेब (Mancozeb) 2.5 ग्राम प्रति लीटर पानी में मिलाकर स्प्रे करें।
⚠️ *अस्वीकरण:* यह एआई सुझाव है, गंभीर समस्या में कृषि विशेषज्ञ से सलाह लें।""",
                language="hi",
            )
            logger.info("Sample seed queries created successfully.")
    except Exception as e:
        logger.warning(f"Could not seed sample data: {e}")


def create_app():
    app = Flask(__name__)

    # Enable CORS for frontend clients
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize Database
    init_db()
    seed_sample_data()

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(crop_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(plant_bp)
    app.register_blueprint(history_bp)

    # Health check route
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "KisanMitra AI Backend",
            "version": "1.0.0",
        }), 200

    # Global JSON error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": str(e.description or "Bad request")}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": str(e.description or "Resource not found")}), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"error": "File size too large (Maximum allowed is 5MB)."}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error. Please try again later."}), 500

    return app


app = create_app()

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    print(f"[KisanMitra AI] Backend running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)

