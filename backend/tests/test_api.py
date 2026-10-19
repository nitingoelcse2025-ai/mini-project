"""
Pytest integration test suite for KisanMitra AI Backend.
Covers:
1. /api/health endpoint
2. Chat validation errors (empty, wrong type, length limits, message count limits)
3. Successful crop-advice call with mocked AI & source verification
4. Plant-check wrong-type (.txt) and too-large (>5MB) rejection
5. Plant-check HTTP 503 when AI fails (no fake diagnosis)
6. Weather HTTP 404 for unknown city
7. Weather save=false not writing to history vs save=true writing to history
8. History list and delete including 404 for non-existent record
"""

import io
import os
import pytest
from unittest.mock import patch

# Configure test database before loading application
test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_kisanmitra.db")
os.environ["DATABASE_PATH"] = test_db_path
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"

import app as flask_app
from database import init_db, get_queries, save_query, get_db_connection
from limiter import ai_limiter


@pytest.fixture(autouse=True)
def setup_test_db():
    """Sets up an isolated clean SQLite database for tests and resets rate limiter."""
    ai_limiter.requests.clear()
    init_db()
    # Clean tables
    with get_db_connection() as conn:
        conn.execute("DELETE FROM queries")
        conn.commit()
    yield
    # Cleanup after test
    with get_db_connection() as conn:
        conn.execute("DELETE FROM queries")
        conn.commit()


@pytest.fixture
def client():
    """Flask test client."""
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as client:
        yield client


# =====================================================================
# 1. Health Check Test
# =====================================================================

def test_health_check(client):
    """Tests GET /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "KisanMitra" in data["service"]


# =====================================================================
# 2. Chat Validation Error Tests
# =====================================================================

def test_chat_validation_missing_messages(client):
    """Tests that missing or non-list messages returns 400."""
    res1 = client.post("/api/chat", json={})
    assert res1.status_code == 400
    assert "messages is required" in res1.get_json()["error"]

    res2 = client.post("/api/chat", json={"messages": "not-a-list"})
    assert res2.status_code == 400
    assert "messages is required" in res2.get_json()["error"]


def test_chat_validation_empty_user_message(client):
    """Tests that an empty latest message returns 400."""
    res = client.post("/api/chat", json={
        "messages": [{"role": "user", "content": "   "}]
    })
    assert res.status_code == 400
    assert "cannot be empty" in res.get_json()["error"]


def test_chat_validation_too_many_messages(client):
    """Tests that exceeding 20 messages returns 400."""
    too_many = [{"role": "user", "content": f"msg {i}"} for i in range(21)]
    res = client.post("/api/chat", json={"messages": too_many})
    assert res.status_code == 400
    assert "exceed 20 messages" in res.get_json()["error"]


def test_chat_validation_message_too_long(client):
    """Tests that messages exceeding 1000 characters return 400."""
    long_msg = "A" * 1005
    res = client.post("/api/chat", json={
        "messages": [{"role": "user", "content": long_msg}]
    })
    assert res.status_code == 400
    assert "1000 characters" in res.get_json()["error"]


# =====================================================================
# 3. Successful Crop Advice Call Test
# =====================================================================

@patch("routes.crop.generate_crop_advice")
def test_successful_crop_advice(mock_crop_ai, client):
    """Tests successful crop advice response and persistence when source is AI."""
    mock_crop_ai.return_value = {
        "text": "### 🌾 गेहूं की कृषि सलाह\n• समय पर बुवाई करें।",
        "source": "ai",
    }

    payload = {
        "crop": "Wheat",
        "season": "Rabi",
        "soil": "Loamy",
        "question": "How much DAP to use?",
        "language": "hi",
    }

    res = client.post("/api/crop-advice", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["crop"] == "Wheat"
    assert data["season"] == "Rabi"
    assert data["source"] == "ai"
    assert "गेहूं की कृषि सलाह" in data["advice"]

    # Verify query was saved to history table
    records = get_queries(query_type="crop")
    assert len(records) == 1
    assert "Wheat" in records[0]["question"]


# =====================================================================
# 4. Plant Check: Wrong Type & Too Large Rejection
# =====================================================================

def test_plant_check_missing_image(client):
    """Tests that missing image field returns 400."""
    res = client.post("/api/plant-check", data={})
    assert res.status_code == 400
    assert "No image file provided" in res.get_json()["error"]


def test_plant_check_invalid_extension(client):
    """Tests that uploading non-image extensions (.txt) returns 400."""
    fake_txt = (io.BytesIO(b"Hello world text"), "notes.txt")
    res = client.post(
        "/api/plant-check",
        data={"image": fake_txt},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400
    assert "Invalid image format" in res.get_json()["error"]


def test_plant_check_too_large(client):
    """Tests that uploading an image > 5MB is rejected with 400 or 413."""
    six_mb = io.BytesIO(b"0" * (6 * 1024 * 1024))
    res = client.post(
        "/api/plant-check",
        data={"image": (six_mb, "large_leaf.jpg")},
        content_type="multipart/form-data",
    )
    assert res.status_code in [400, 413]
    err = res.get_json()["error"]
    assert "5MB" in err or "File size too large" in err


# =====================================================================
# 5. Plant Check: HTTP 503 When AI Fails (No Fake Diagnosis)
# =====================================================================

@patch("routes.plant.generate_plant_diagnosis")
def test_plant_check_503_when_ai_fails(mock_plant_ai, client):
    """Tests that if Gemini vision fails, endpoint returns 503 and never returns fake diagnosis."""
    mock_plant_ai.return_value = {"text": "", "source": "fallback"}

    valid_img = (io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01"), "leaf.jpg")
    res = client.post(
        "/api/plant-check",
        data={"image": valid_img, "crop": "Tomato"},
        content_type="multipart/form-data",
    )
    assert res.status_code == 503
    data = res.get_json()
    assert "unavailable" in data["error"].lower()

    # Verify no record was saved to history
    records = get_queries(query_type="plant")
    assert len(records) == 0


# =====================================================================
# 6. Weather: HTTP 404 for Unknown City
# =====================================================================

@patch("routes.weather.geocode_location")
def test_weather_unknown_city_404(mock_geo, client):
    """Tests that unknown city geocoding returns 404."""
    mock_geo.return_value = None
    res = client.get("/api/weather?city=UnknownFictionalCity999")
    assert res.status_code == 404
    data = res.get_json()
    assert "Could not find coordinates" in data["error"]


# =====================================================================
# 7. Weather: save=false Does NOT Write to History, save=true Does
# =====================================================================

@patch("routes.weather.geocode_location")
@patch("routes.weather.fetch_weather")
@patch("routes.weather.generate_weather_tip")
def test_weather_save_parameter_behavior(mock_tip, mock_fetch, mock_geo, client):
    """Tests that GET /api/weather writes to history ONLY when save=true."""
    mock_geo.return_value = (26.91, 75.78, "Jaipur, Rajasthan, India")
    mock_fetch.return_value = {
        "location_name": "Jaipur, Rajasthan, India",
        "current": {
            "temperature": 32,
            "humidity": 45,
            "wind_speed": 12,
            "condition": "साफ आसमान",
            "icon": "sunny",
        },
    }
    mock_tip.return_value = {
        "text": "☀️ मौसम साफ है। सिंचाई के लिए अनुकूल समय है।",
        "source": "ai",
    }

    # 1. Automatic reload or restore: save=false
    res1 = client.get("/api/weather?city=Jaipur&save=false")
    assert res1.status_code == 200
    assert res1.get_json()["source"] == "ai"
    assert len(get_queries(query_type="weather")) == 0

    # 2. Omitted save param (default false)
    res2 = client.get("/api/weather?city=Jaipur")
    assert res2.status_code == 200
    assert len(get_queries(query_type="weather")) == 0

    # 3. User-initiated search: save=true
    res3 = client.get("/api/weather?city=Jaipur&save=true")
    assert res3.status_code == 200
    records = get_queries(query_type="weather")
    assert len(records) == 1
    assert "Jaipur" in records[0]["question"]


# =====================================================================
# 8. History: List, Delete, and 404
# =====================================================================

def test_history_list_and_delete(client):
    """Tests listing queries, deleting by ID, and deleting non-existent ID."""
    q_id = save_query(
        query_type="chat",
        question="What fertilizer for wheat?",
        response="Use balanced DAP and Urea.",
        language="en",
    )

    # 1. List history
    list_res = client.get("/api/history")
    assert list_res.status_code == 200
    data = list_res.get_json()
    assert data["count"] >= 1
    assert any(item["id"] == q_id for item in data["history"])

    # 2. Delete existing record
    del_res = client.delete(f"/api/history/{q_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["id"] == q_id

    # Verify deleted
    assert not any(item["id"] == q_id for item in get_queries())

    # 3. Delete non-existent record -> 404
    del_404_res = client.delete("/api/history/999999")
    assert del_404_res.status_code == 404
    assert "not found" in del_404_res.get_json()["error"].lower()
