"""
Automated Integration Tests for Razors-n-scissors WhatsApp Webhook (Twilio Sandbox)
INT428 Course Project — Group 13 — Suman Saha
"""

import pytest
from app.whatsapp_bot import (
    handle_whatsapp_message,
    _build_twiml,
    _clean_phone,
    health,
    _user_sessions
)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Reset session map before each test for test isolation."""
    _user_sessions.clear()
    yield
    _user_sessions.clear()


def test_whatsapp_health_check():
    """Verifies the health check endpoint returns 200 and healthy status."""
    res = health()
    assert res["status"] == "healthy"
    assert "Razors-n-scissors" in res["salon"]
    assert res["whatsapp_channel"] == "Twilio Sandbox"


def test_whatsapp_twiml_builder():
    """Verifies XML special character escaping in TwiML response."""
    raw = "Hair & Beard Cut <Special> 'Promo' \"Discount\""
    xml = _build_twiml(raw)
    assert "<Response>" in xml
    assert "<Message>" in xml
    assert "&amp;" in xml
    assert "&lt;" in xml
    assert "&gt;" in xml


def test_clean_phone_utility():
    """Verifies 10-digit phone extraction from Twilio from header."""
    assert _clean_phone("whatsapp:+916284421638") == "6284421638"
    assert _clean_phone("+91-9876543210") == "9876543210"
    assert _clean_phone("invalid") == ""


def test_whatsapp_webhook_empty_body_greeting():
    """Empty body sends default Razors-n-scissors greeting in Twilio TwiML format."""
    result = handle_whatsapp_message(
        from_user="whatsapp:+916284421638",
        body_text="",
        profile_name="Suman"
    )
    assert "<Response>" in result["twiml"]
    assert "Razors-n-scissors" in result["reply"]
    assert "services" in result["reply"].lower()


def test_whatsapp_webhook_pricing_query():
    """Asking for haircut price returns real Razors-n-scissors rate (₹100)."""
    result = handle_whatsapp_message(
        from_user="whatsapp:+916284421638",
        body_text="How much does a haircut cost?",
        profile_name="Suman"
    )
    assert "100" in result["reply"]
    assert "<Response>" in result["twiml"]


def test_whatsapp_webhook_medical_safety_guardrail():
    """Ensures clinical/medical queries are refused safely over WhatsApp."""
    result = handle_whatsapp_message(
        from_user="whatsapp:+916284421638",
        body_text="My scalp has severe red pus and infection, prescribe an antibiotic ointment.",
        profile_name="Student"
    )
    assert "dermatologist" in result["reply"].lower() or "medical" in result["reply"].lower()


def test_whatsapp_multi_turn_booking_flow():
    """
    Verifies multi-turn booking state tracking over WhatsApp without barber selection:
    Turn 1: 'Book appointment' -> asks which service
    Turn 2: 'Hair Cut' -> asks which date
    Turn 3: 'tomorrow' -> asks what time
    """
    test_user = "whatsapp:+919888877777"

    # Turn 1: Trigger booking
    r1 = handle_whatsapp_message(from_user=test_user, body_text="I want to book an appointment")
    assert "Which service" in r1["reply"] or "service" in r1["reply"].lower()

    # Turn 2: Choose service
    r2 = handle_whatsapp_message(from_user=test_user, body_text="Hair Cut")
    assert "date" in r2["reply"].lower()

    # Turn 3: Choose date
    r3 = handle_whatsapp_message(from_user=test_user, body_text="tomorrow")
    assert "time" in r3["reply"].lower() or "slot" in r3["reply"].lower()


def test_whatsapp_session_reset():
    """Keywords like 'reset' or 'restart' clear the conversational state."""
    test_user = "whatsapp:+919888866666"

    # Start booking
    handle_whatsapp_message(from_user=test_user, body_text="Book appointment")
    # Reset
    r_reset = handle_whatsapp_message(from_user=test_user, body_text="reset")
    assert "reset" in r_reset["reply"].lower()
