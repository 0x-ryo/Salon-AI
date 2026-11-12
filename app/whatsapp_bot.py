"""
Razors-n-scissors – WhatsApp Webhook (Twilio Sandbox)
INT428 Course Project — Group 13 — Suman Saha

Handles inbound WhatsApp messages from Twilio WhatsApp Sandbox:
1. Multi-turn session tracking per WhatsApp user (phone number)
2. Auto-binds customer phone and profile name from Twilio metadata
3. Routes to HybridSalonAgent (Guardrails -> Intent -> Slot Filling / Semantic Retrieval)
4. Returns compliant Twilio TwiML XML messaging responses
5. Clean modular structure for zero-dependency unit and integration testing
"""

import os
import sys
import re
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.hybrid_agent import HybridSalonAgent
try:
    from salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS
except Exception:
    try:
        from app.salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS
    except Exception:
        SALON_NAME = "Razors-n-scissors"
        PHONE_WHATSAPP = "+91 9877175449"
        ADDRESS = "BH-5, Lovely Professional University Campus, Phagwara, Punjab"

app = FastAPI(title="Razors-n-scissors WhatsApp Bot (Twilio Sandbox)")

# Per-user conversational agent session map: user_key -> HybridSalonAgent
_user_sessions: dict[str, HybridSalonAgent] = {}


def get_agent_for_user(user_id: str) -> HybridSalonAgent:
    """Retrieves or creates a dedicated hybrid agent session for a WhatsApp sender."""
    if user_id not in _user_sessions:
        _user_sessions[user_id] = HybridSalonAgent()
    return _user_sessions[user_id]


def _build_twiml(message: str) -> str:
    """Wraps plain text in valid Twilio TwiML MessagingResponse XML."""
    safe = (
        message.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
               .replace('"', "&quot;")
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        f"    <Message>{safe}</Message>\n"
        "</Response>"
    )


def _clean_phone(from_str: str) -> str:
    """Extracts a 10-digit phone number from Twilio From format (whatsapp:+919877175449)."""
    match = re.search(r"([6789]\d{9})\b", from_str)
    return match.group(1) if match else ""


def handle_whatsapp_message(from_user: str, body_text: str = "", profile_name: str = "") -> dict:
    """
    Core business logic processing inbound WhatsApp messages.
    Returns: {"twiml": str, "reply": str, "sender": str}
    """
    clean_sender = from_user.replace("whatsapp:", "").strip()
    extracted_phone = _clean_phone(clean_sender)

    # Get user session agent
    agent = get_agent_for_user(clean_sender)

    # Pre-populate slots with Twilio caller identity if missing
    if extracted_phone and not agent.rule_engine.slots.get("phone"):
        agent.rule_engine.slots["phone"] = extracted_phone
    if profile_name and not agent.rule_engine.slots.get("customer_name"):
        agent.rule_engine.slots["customer_name"] = profile_name

    body_clean = (body_text or "").strip()

    # Empty body / greeting trigger
    if not body_clean:
        reply = (
            f"👋 Welcome to *{SALON_NAME}* (BH-5, LPU)!\n\n"
            "I can help you:\n"
            "• 💈 Check prices & services (type *services* or *rates*)\n"
            "• 📅 Book an appointment (type *book haircut*)\n"
            "• ⏰ Check salon timings (type *timings*)\n"
            "• ❌ Cancel a booking (type *cancel*)\n"
            "• 🤝 Speak to staff (type *manager*)"
        )
        return {
            "twiml": _build_twiml(reply),
            "reply": reply,
            "sender": clean_sender
        }

    # Handle session reset keyword
    if body_clean.lower() in ["reset", "restart", "start over"]:
        agent.reset_session()
        reply = f"🔄 Conversation session reset! How can I assist you at {SALON_NAME} today?"
        return {
            "twiml": _build_twiml(reply),
            "reply": reply,
            "sender": clean_sender
        }

    # Process user query through Hybrid Salon Agent
    result = agent.handle_message(body_clean, engine_mode="Hybrid")
    reply = result.get("response", "I'm sorry, I couldn't process that. Please try again.")

    return {
        "twiml": _build_twiml(reply),
        "reply": reply,
        "sender": clean_sender,
        "trace": result.get("trace")
    }


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp Webhook.
    Accepts both application/x-www-form-urlencoded (Twilio default)
    and application/json (for API testing).
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
        from_user = data.get("From", "+919877175449")
        body_text = data.get("Body", "")
        profile_name = data.get("ProfileName", "")
    else:
        form_data = await request.form()
        from_user = form_data.get("From", "+919877175449")
        body_text = form_data.get("Body", "")
        profile_name = form_data.get("ProfileName", "")

    result = handle_whatsapp_message(from_user, body_text, profile_name)
    return Response(content=result["twiml"], media_type="application/xml")


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "salon": SALON_NAME,
        "location": ADDRESS,
        "whatsapp_channel": "Twilio Sandbox",
        "active_user_sessions": len(_user_sessions)
    }
