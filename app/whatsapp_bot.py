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
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, JSONResponse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.hybrid_agent import HybridSalonAgent
from engine.rule_engine import get_master_menu
from database.db import (
    init_db, get_all_appointments, get_live_metrics, update_appointment_status,
    resolve_handover, resolve_complaint, get_all_complaints, get_handover_queue
)
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

# Ensure SQLite schema and initial salon services are initialized
try:
    init_db()
except Exception as _e:
    print(f"[DB Init Note]: {_e}")

@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception as _e:
        print(f"[DB Startup Note]: {_e}")

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

    # Empty body / greeting trigger -> Return interactive master menu
    if not body_clean:
        reply = get_master_menu()
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


@app.get("/whatsapp/meta-webhook")
async def meta_webhook_verification(request: Request):
    """
    Meta WhatsApp Cloud API Webhook Verification Challenge.
    Meta sends hub.mode, hub.verify_token, hub.challenge.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    expected_token = os.environ.get("META_VERIFY_TOKEN", "salon_ai_meta_2026")

    if mode == "subscribe" and token == expected_token:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verification token mismatch", status_code=403)


@app.post("/whatsapp/meta-webhook")
async def meta_webhook_handler(request: Request):
    """
    Meta WhatsApp Cloud API Message Receiver.
    Accepts incoming message JSON, invokes Hybrid Agent, and replies via Meta Graph API.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            messages = val.get("messages", [])
            metadata = val.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", os.environ.get("META_PHONE_NUMBER_ID", ""))
            contacts = val.get("contacts", [])
            profile_name = contacts[0].get("profile", {}).get("name", "") if contacts else ""

            for msg in messages:
                from_user = msg.get("from", "")
                msg_type = msg.get("type", "")
                body_text = msg.get("text", {}).get("body", "") if msg_type == "text" else ""

                if from_user and body_text:
                    result = handle_whatsapp_message(from_user, body_text, profile_name)
                    reply_text = result.get("reply", "")

                    # Send outgoing reply via Meta Graph API
                    access_token = os.environ.get("META_ACCESS_TOKEN", "")
                    if access_token and phone_number_id:
                        url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
                        headers = {
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"
                        }
                        data = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": from_user,
                            "type": "text",
                            "text": {"body": reply_text}
                        }
                        try:
                            async with httpx.AsyncClient() as client:
                                await client.post(url, headers=headers, json=data, timeout=10.0)
                        except Exception as e:
                            print(f"[Meta Graph API Error]: {e}")

    return {"status": "ok"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "salon": SALON_NAME,
        "location": ADDRESS,
        "whatsapp_channel": "Twilio Sandbox",
        "active_user_sessions": len(_user_sessions)
    }


# ================= REAL-TIME DASHBOARD REST SYNC APIS =================

@app.get("/api/appointments")
def api_get_appointments():
    """Returns all salon appointments for real-time dashboard sync."""
    try:
        return get_all_appointments()
    except Exception as e:
        try:
            init_db()
            return get_all_appointments()
        except Exception:
            return []


@app.get("/api/metrics")
def api_get_metrics():
    """Returns real-time KPIs and revenue metrics for salon owner."""
    try:
        return get_live_metrics()
    except Exception as e:
        try:
            init_db()
            return get_live_metrics()
        except Exception:
            return {
                "total_appointments": 0,
                "today_appointments": 0,
                "total_revenue": 0,
                "pending_handovers": 0,
                "open_complaints": 0,
                "popular_services": [],
                "recent_appointments": []
            }


@app.get("/api/handovers")
def api_get_handovers():
    """Returns pending human staff handovers."""
    try:
        return get_handover_queue()
    except Exception:
        return []


@app.get("/api/complaints")
def api_get_complaints():
    """Returns customer complaints desk tickets."""
    try:
        return get_all_complaints()
    except Exception:
        return []


@app.post("/api/action/status")
async def api_update_status(request: Request):
    """Updates appointment status (e.g. COMPLETED, CANCELLED, BOOKED)."""
    data = await request.json()
    app_id = int(data.get("id", 0))
    new_status = data.get("status", "COMPLETED")
    success = update_appointment_status(app_id, new_status)
    return {"success": success, "id": app_id, "status": new_status}


@app.post("/api/action/handover")
async def api_resolve_handover(request: Request):
    """Resolves an escalation handover."""
    data = await request.json()
    ho_id = int(data.get("id", 0))
    resolve_handover(ho_id)
    return {"success": True, "id": ho_id}


@app.post("/api/action/complaint")
async def api_resolve_complaint(request: Request):
    """Resolves a customer complaint ticket with notes."""
    data = await request.json()
    cid = int(data.get("id", 0))
    notes = data.get("notes", "Resolved by salon management")
    resolve_complaint(cid, notes)
    return {"success": True, "id": cid}
