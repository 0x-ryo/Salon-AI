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
import time
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response, JSONResponse, HTMLResponse

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
        PHONE_WHATSAPP = "+91 6284421638"
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
    """Extracts a 10-digit phone number from Twilio From format (whatsapp:+916284421638)."""
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
        from_user = data.get("From", "+916284421638")
        body_text = data.get("Body", "")
        profile_name = data.get("ProfileName", "")
    else:
        form_data = await request.form()
        from_user = form_data.get("From", "+916284421638")
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


@app.post("/api/action/book")
async def api_book_appointment(request: Request):
    """Creates a new appointment via REST API."""
    try:
        data = await request.json()
        from database.db import book_appointment
        success, msg, app_id = book_appointment(
            customer_name=data.get("customer_name", "Walk-in"),
            phone=data.get("phone", PHONE_WHATSAPP.replace("+", "").replace(" ", "")),
            service_id=data.get("service_id", 1),
            barber_id=data.get("barber_id", 1),
            date_str=data.get("date_str", "2026-11-14"),
            time_str=data.get("time_str", "10:00")
        )
        return {"success": success, "message": msg, "id": app_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


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


# ================= REAL-NUMBER WHATSAPP CLOUD GATEWAY (NEONIZE) =================
import threading

WA_TARGET_PHONE = os.environ.get("WA_TARGET_PHONE", PHONE_WHATSAPP.replace("+", "").replace(" ", ""))
NEONIZE_DB = os.environ.get("DATABASE_URL", "")
if not NEONIZE_DB:
    # Local fallback to SQLite database file
    NEONIZE_DB = os.path.join(PROJECT_ROOT, "database", "neonize_session.sqlite3")
elif NEONIZE_DB.startswith("postgresql://"):
    # Convert postgresql:// to postgres:// for Go lib/pq driver
    NEONIZE_DB = NEONIZE_DB.replace("postgresql://", "postgres://", 1)

pairing_state = {
    "status": "Initializing",
    "phone": WA_TARGET_PHONE,
    "code": "",
    "qr_raw": "",
    "connected": False,
    "error": None,
    "messages_handled": 0,
    "code_timestamp": time.time(),
    "db": "PostgreSQL (Render Persistent)" if "postgres" in NEONIZE_DB else "SQLite"
}

_neonize_client = None

def _run_neonize_gateway():
    global _neonize_client
    try:
        import neonize
        from neonize.client import NewClient
        from neonize.events import ConnectedEv, MessageEv, PairStatusEv
        from neonize.utils import extract_text
    except Exception as e:
        pairing_state["status"] = "Disabled"
        pairing_state["error"] = f"Neonize library not loaded: {e}"
        print(f"[Neonize Setup Notice]: {e}")
        return

    while True:
        try:
            if pairing_state.get("connected"):
                time.sleep(5)
                continue

            print(f"[Neonize Gateway]: Starting client with phone +{WA_TARGET_PHONE}...")
            client = NewClient(NEONIZE_DB)
            _neonize_client = client

            @client.qr
            def on_qr(c: NewClient, qr_data: bytes):
                try:
                    raw_qr = qr_data.decode("utf-8", errors="ignore")
                    pairing_state["qr_raw"] = raw_qr
                    if not c.is_logged_in:
                        try:
                            code = c.PairPhone(WA_TARGET_PHONE, show_push_notification=True)
                            pairing_state["code"] = code
                            pairing_state["status"] = "Ready to Pair"
                            pairing_state["code_timestamp"] = time.time()
                            print("==================================================")
                            print(f"[WhatsApp Pairing Code]: {code} (for +{WA_TARGET_PHONE})")
                            print("==================================================")
                        except Exception as err:
                            pairing_state["error"] = str(err)
                            print(f"[Neonize PairPhone Error]: {err}")
                except Exception as outer_err:
                    pairing_state["error"] = str(outer_err)
                    print(f"[Neonize on_qr Error]: {outer_err}")

            @client.event(ConnectedEv)
            def on_connected(c: NewClient, ev: ConnectedEv):
                pairing_state["connected"] = True
                pairing_state["status"] = "Connected"
                pairing_state["error"] = None
                print(f"🎉 [WhatsApp Cloud Gateway]: Live & Connected 24/7 as +{WA_TARGET_PHONE}!")

            @client.event(PairStatusEv)
            def on_pair_status(c: NewClient, ev: PairStatusEv):
                print(f"[Neonize PairStatus]: {ev}")

            @client.event(MessageEv)
            def on_message(c: NewClient, msg: MessageEv):
                try:
                    if msg.Info.MessageSource.IsFromMe:
                        return

                    body_text = extract_text(msg.Message)
                    if not body_text:
                        return

                    sender_user = msg.Info.MessageSource.Sender.User or ""
                    profile_name = msg.Info.Pushname or ""

                    print(f"[WhatsApp Inbound]: +{sender_user} ({profile_name}): '{body_text}'")
                    result = handle_whatsapp_message(sender_user, body_text, profile_name)
                    reply_text = result.get("reply", "")

                    if reply_text:
                        c.reply_message(reply_text, msg)
                        pairing_state["messages_handled"] += 1
                        print(f"[WhatsApp Reply Sent]: '{reply_text[:60]}...'")
                except Exception as mex:
                    print(f"[WhatsApp Message Error]: {mex}")

            pairing_state["status"] = "Connecting..."
            client.connect()
            print("[Neonize Gateway]: Connect session ended, restarting in 3s...")
        except Exception as ce:
            pairing_state["status"] = "Error"
            pairing_state["error"] = str(ce)
            print(f"[Neonize Client Run Error]: {ce}")

        time.sleep(3)


# Start gateway thread on startup
@app.on_event("startup")
def start_gateway_background():
    threading.Thread(target=_run_neonize_gateway, daemon=True, name="WhatsAppNeonizeGateway").start()


@app.get("/api/pair-status")
def api_pair_status():
    """Returns current pairing code and WhatsApp cloud gateway connection status."""
    return pairing_state


@app.post("/api/pair-refresh")
def api_pair_refresh():
    """Manually requests a fresh 8-digit pairing code or triggers reconnect."""
    global _neonize_client
    if pairing_state.get("connected"):
        return {"success": False, "message": "Already connected 24/7"}

    if _neonize_client:
        try:
            code = _neonize_client.PairPhone(WA_TARGET_PHONE, show_push_notification=True)
            pairing_state["code"] = code
            pairing_state["status"] = "Ready to Pair"
            pairing_state["code_timestamp"] = time.time()
            return {"success": True, "code": code}
        except Exception as e:
            try:
                _neonize_client.disconnect()
            except Exception:
                pass
            return {"success": False, "error": str(e), "message": "Reconnecting gateway..."}
    return {"success": False, "error": "Gateway starting up"}


@app.get("/pair", response_class=HTMLResponse)
def pair_page():
    """Mobile-friendly luxury gold UI to link WhatsApp to the 24/7 cloud bot."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SALON_NAME} | WhatsApp Cloud Pairing</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --gold: #D4AF37;
            --gold-light: #F3E5AB;
            --bg-dark: #0D1117;
            --card-bg: #161B22;
            --border: #30363D;
            --text-main: #F0F6FC;
            --text-sub: #8B949E;
            --success: #2EA043;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 20px;
            max-width: 500px;
            width: 100%;
            padding: 30px 24px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.6);
            text-align: center;
        }}
        .badge-cloud {{
            display: inline-block;
            background: rgba(212, 175, 55, 0.15);
            color: var(--gold);
            border: 1px solid var(--gold);
            padding: 5px 14px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        h1 {{
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 4px;
            color: #FFFFFF;
        }}
        .subtitle {{
            color: var(--text-sub);
            font-size: 0.85rem;
            margin-bottom: 16px;
        }}
        .code-box {{
            background: #090D12;
            border: 2px dashed var(--gold);
            border-radius: 14px;
            padding: 18px 12px;
            margin: 14px 0;
        }}
        .code-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--gold-light);
            margin-bottom: 6px;
        }}
        .code-display {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: 4px;
            color: var(--gold);
            user-select: all;
        }}
        .timer {{
            font-size: 0.8rem;
            color: #F59E0B;
            margin-top: 6px;
            font-weight: 600;
        }}
        .qr-container {{
            background: #FFFFFF;
            padding: 12px;
            border-radius: 14px;
            display: inline-block;
            margin: 12px auto;
            border: 2px solid var(--gold);
        }}
        .qr-container img {{
            display: block;
            width: 200px;
            height: 200px;
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 600;
            margin: 8px 0 14px 0;
        }}
        .status-waiting {{
            background: rgba(245, 158, 11, 0.15);
            color: #F59E0B;
            border: 1px solid #F59E0B;
        }}
        .status-connected {{
            background: rgba(46, 160, 67, 0.2);
            color: #3FB950;
            border: 1px solid #2EA043;
        }}
        .btn {{
            background: linear-gradient(135deg, #D4AF37 0%, #AA820A 100%);
            color: #000;
            font-weight: 700;
            border: none;
            padding: 11px 20px;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            margin-bottom: 8px;
        }}
        .btn:hover {{
            filter: brightness(1.1);
            transform: translateY(-1px);
        }}
        .btn-outline {{
            background: transparent;
            color: var(--gold);
            border: 1px solid var(--gold);
            margin-bottom: 14px;
        }}
        .btn-outline:hover {{
            background: rgba(212, 175, 55, 0.15);
        }}
        .instructions {{
            text-align: left;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 14px 16px;
            margin-top: 14px;
            font-size: 0.82rem;
            color: #C9D1D9;
            line-height: 1.5;
        }}
        .instructions ol {{
            margin-left: 18px;
        }}
        .instructions li {{
            margin-bottom: 4px;
        }}
        .tabs {{
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .tab-btn {{
            flex: 1;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: #111418;
            color: var(--text-sub);
            cursor: pointer;
            font-weight: 600;
            font-size: 0.82rem;
        }}
        .tab-btn.active {{
            background: rgba(212, 175, 55, 0.15);
            border-color: var(--gold);
            color: var(--gold);
        }}
        .footer {{
            margin-top: 20px;
            font-size: 0.72rem;
            color: var(--text-sub);
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge-cloud">⚡ 24/7 CLOUD BOT ENGINE</span>
        <h1>{SALON_NAME}</h1>
        <p class="subtitle">WhatsApp Multi-Device Link for <strong>+{WA_TARGET_PHONE}</strong></p>

        <div id="statusBadge" class="status-badge status-waiting">
            <span>●</span> <span id="statusText">Checking WhatsApp Cloud Status...</span>
        </div>

        <div class="tabs" id="tabGroup">
            <button class="tab-btn active" id="tabCodeBtn" onclick="switchTab('code')">🔢 8-Digit Code</button>
            <button class="tab-btn" id="tabQrBtn" onclick="switchTab('qr')">📷 QR Code Scan</button>
        </div>

        <!-- CODE TAB -->
        <div id="codeView">
            <div class="code-box" id="codeContainer">
                <div class="code-label">Enter this 8-Character Pairing Code:</div>
                <div class="code-display" id="codeText">••••••••</div>
                <div class="timer" id="timerDisplay">⏱️ Code valid for: <span id="secondsLeft">90</span>s</div>
            </div>

            <button class="btn" id="copyBtn" onclick="copyCode()">📋 Copy Pairing Code</button>
            <button class="btn btn-outline" id="refreshBtn" onclick="refreshCode()">🔄 Generate Fresh Code</button>

            <div class="instructions">
                <strong>📲 How to link with Code:</strong>
                <ol>
                    <li>Open <strong>WhatsApp / WhatsApp Business</strong> on your phone.</li>
                    <li>Tap <strong>Settings</strong> (or ⋮ <strong>3 dots</strong>) ➔ <strong>Linked Devices</strong>.</li>
                    <li>Tap <strong>Link a Device</strong>.</li>
                    <li>Tap <strong>"Link with phone number instead"</strong> at the bottom.</li>
                    <li>Enter the code above!</li>
                </ol>
            </div>
        </div>

        <!-- QR TAB -->
        <div id="qrView" style="display: none;">
            <div class="qr-container" id="qrContainer">
                <img id="qrImg" src="" alt="WhatsApp QR Code" />
            </div>
            <p style="font-size: 0.8rem; color: var(--text-sub); margin-bottom: 12px;">Point your phone camera at this QR code</p>
            <button class="btn btn-outline" onclick="refreshCode()">🔄 Refresh QR Code</button>

            <div class="instructions">
                <strong>📷 How to link with QR:</strong>
                <ol>
                    <li>Open <strong>WhatsApp Business</strong> on your phone.</li>
                    <li>Tap <strong>Settings / ⋮</strong> ➔ <strong>Linked Devices</strong>.</li>
                    <li>Tap <strong>Link a Device</strong>.</li>
                    <li>Point camera at the QR code above to link instantly!</li>
                </ol>
            </div>
        </div>

        <div class="footer">
            No laptop required · Powered by Render Cloud & PostgreSQL · INT428 Project 13
        </div>
    </div>

    <script>
        let currentCode = "";
        let codeTime = 0;
        let countdownTimer = null;

        function switchTab(mode) {{
            const codeView = document.getElementById('codeView');
            const qrView = document.getElementById('qrView');
            const tabCodeBtn = document.getElementById('tabCodeBtn');
            const tabQrBtn = document.getElementById('tabQrBtn');

            if (mode === 'code') {{
                codeView.style.display = 'block';
                qrView.style.display = 'none';
                tabCodeBtn.className = 'tab-btn active';
                tabQrBtn.className = 'tab-btn';
            }} else {{
                codeView.style.display = 'none';
                qrView.style.display = 'block';
                tabCodeBtn.className = 'tab-btn';
                tabQrBtn.className = 'tab-btn active';
            }}
        }}

        function startCountdown() {{
            if (countdownTimer) clearInterval(countdownTimer);
            const secondsLeftSpan = document.getElementById('secondsLeft');
            countdownTimer = setInterval(() => {{
                const elapsed = Math.floor(Date.now() / 1000) - codeTime;
                const remaining = Math.max(0, 100 - elapsed);
                secondsLeftSpan.innerText = remaining;
                if (remaining <= 0) {{
                    document.getElementById('timerDisplay').innerText = "⚠️ Code expired! Click 'Generate Fresh Code'";
                }} else {{
                    document.getElementById('timerDisplay').innerHTML = `⏱️ Code valid for: <strong>${{remaining}}</strong>s`;
                }}
            }}, 1000);
        }}

        async function checkStatus() {{
            try {{
                const res = await fetch('/api/pair-status');
                const data = await res.json();
                const badge = document.getElementById('statusBadge');
                const statusText = document.getElementById('statusText');
                const codeText = document.getElementById('codeText');
                const copyBtn = document.getElementById('copyBtn');
                const qrImg = document.getElementById('qrImg');

                if (data.connected) {{
                    badge.className = "status-badge status-connected";
                    statusText.innerHTML = "🟢 WhatsApp Bot Active 24/7 in Cloud!";
                    codeText.innerHTML = "CONNECTED";
                    codeText.style.fontSize = "1.8rem";
                    codeText.style.color = "#3FB950";
                    copyBtn.style.display = "none";
                    document.getElementById('refreshBtn').style.display = "none";
                    document.getElementById('timerDisplay').style.display = "none";
                    document.getElementById('tabGroup').style.display = "none";
                }} else if (data.code) {{
                    if (data.code !== currentCode) {{
                        currentCode = data.code;
                        codeText.innerText = data.code;
                        codeTime = Math.floor(data.code_timestamp || (Date.now() / 1000));
                        startCountdown();
                    }}
                    badge.className = "status-badge status-waiting";
                    statusText.innerText = "Ready to Pair (Waiting for phone)";
                    copyBtn.style.display = "block";

                    if (data.qr_raw) {{
                        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${{encodeURIComponent(data.qr_raw)}}`;
                    }}
                }} else {{
                    statusText.innerText = data.status || "Connecting to Gateway...";
                }}
            }} catch (e) {{
                console.error("Status poll error:", e);
            }}
        }}

        async function refreshCode() {{
            const btn = document.getElementById('refreshBtn');
            btn.innerText = "⏳ Generating Fresh Code...";
            try {{
                await fetch('/api/pair-refresh', {{ method: 'POST' }});
                setTimeout(checkStatus, 1500);
            }} catch (e) {{
                console.error("Refresh error:", e);
            }}
            setTimeout(() => {{ btn.innerText = "🔄 Generate Fresh Code"; }}, 3000);
        }}

        function copyCode() {{
            if (!currentCode) return;
            navigator.clipboard.writeText(currentCode).then(() => {{
                const btn = document.getElementById('copyBtn');
                btn.innerText = "✅ Copied to Clipboard!";
                setTimeout(() => {{ btn.innerText = "📋 Copy Pairing Code"; }}, 2500);
            }});
        }}

        setInterval(checkStatus, 2500);
        checkStatus();
    </script>
</body>
</html>
"""
