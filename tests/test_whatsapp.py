"""
Automated Integration Tests for Razors-n-scissors WhatsApp Webhook (Twilio Sandbox)
INT428 Course Project — Group 13 — Suman Saha
"""

import pytest
from fastapi.testclient import TestClient
from app.whatsapp_bot import app, _user_sessions

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Reset session map before each test for test isolation."""
    _user_sessions.clear()
    yield
    _user_sessions.clear()


def test_whatsapp_health_check():
    """Verifies the health check endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Razors-n-scissors" in data["salon"]


def test_whatsapp_webhook_empty_body_greeting():
    """Empty body sends default Razors-n-scissors greeting in Twilio TwiML format."""
    payload = {
        "From": "whatsapp:+919877175449",
        "Body": "",
        "ProfileName": "Suman"
    }
    response = client.post("/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    assert "text/xml" in response.headers.get("content-type", "") or "application/xml" in response.headers.get("content-type", "")
    assert "<Response>" in response.text
    assert "Razors-n-scissors" in response.text


def test_whatsapp_webhook_pricing_query():
    """Asking for haircut price returns real Razors-n-scissors rate (₹100)."""
    payload = {
        "From": "whatsapp:+919877175449",
        "Body": "How much does a haircut cost?",
        "ProfileName": "Suman"
    }
    response = client.post("/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    assert "100" in response.text
    assert "<Response>" in response.text


def test_whatsapp_webhook_medical_safety_guardrail():
    """Ensures clinical/medical queries are refused safely over WhatsApp."""
    payload = {
        "From": "whatsapp:+919877175449",
        "Body": "My scalp has severe red pus and infection, prescribe an antibiotic ointment.",
        "ProfileName": "Student"
    }
    response = client.post("/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    assert "dermatologist" in response.text.lower() or "medical" in response.text.lower()


def test_whatsapp_multi_turn_booking_flow():
    """
    Verifies multi-turn booking state tracking over WhatsApp without barber selection:
    Turn 1: 'Book appointment' -> asks which service
    Turn 2: 'Hair Cut' -> asks which date
    Turn 3: 'tomorrow' -> asks what time
    """
    test_user = "whatsapp:+919888877777"

    # Turn 1: Trigger booking
    r1 = client.post("/whatsapp/webhook", json={"From": test_user, "Body": "I want to book an appointment"})
    assert r1.status_code == 200
    assert "Which service" in r1.text or "service" in r1.text.lower()

    # Turn 2: Choose service
    r2 = client.post("/whatsapp/webhook", json={"From": test_user, "Body": "Hair Cut"})
    assert r2.status_code == 200
    assert "date" in r2.text.lower()

    # Turn 3: Choose date
    r3 = client.post("/whatsapp/webhook", json={"From": test_user, "Body": "tomorrow"})
    assert r3.status_code == 200
    assert "time" in r3.text.lower() or "slot" in r3.text.lower()


def test_whatsapp_session_reset():
    """Keywords like 'reset' or 'restart' clear the conversational state."""
    test_user = "whatsapp:+919888866666"

    # Start booking
    client.post("/whatsapp/webhook", json={"From": test_user, "Body": "Book appointment"})
    # Reset
    r_reset = client.post("/whatsapp/webhook", json={"From": test_user, "Body": "reset"})
    assert r_reset.status_code == 200
    assert "reset" in r_reset.text.lower()
