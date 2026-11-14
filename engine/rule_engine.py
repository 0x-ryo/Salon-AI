"""
Approach 1: Classical Rule-Based AI Engine & Finite State Machine (FSM).
Razors-n-scissors Salon (INT428 Project 13)
Implements:
1. Regex & Keyword Pattern Matchers for Intent Classification
2. Slot-Filling Dialogue State Tracker (Service, Date, Time, Contact)
   - Categorized [S1] to [S16] price catalog notation
   - State-aware non-sticky navigation with global escape commands
   - 2-Step Day & Available Time Slot selection
   - Joint Customer Name & Mobile Number extraction
3. Step-by-Step Rule Firing & Explainability Trace (Unit II)
"""

import re
from datetime import datetime, timedelta
from database.db import (
    get_all_services, get_service_by_name_or_id, get_all_barbers, get_available_slots,
    book_appointment, cancel_appointment_by_phone, get_appointments_by_phone,
    log_complaint, add_to_handover_queue
)
try:
    from salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS
except Exception:
    try:
        from app.salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS
    except Exception:
        SALON_NAME = "Razors-n-scissors"
        PHONE_WHATSAPP = "+91 6284421638"
        ADDRESS = "BH-5, Lovely Professional University Campus, Phagwara, Punjab"
        OPERATING_HOURS = "Mon–Sun: 9:00 AM – 9:00 PM"

# Intent Regular Expression Catalog
INTENT_PATTERNS = {
    "greeting": [
        r"\b(hi|hello|hey|good\s*(morning|afternoon|evening)|namaste|salaam)\b"
    ],
    "show_menu": [
        r"\b(menu|options|help|start|main\s*menu|list\s*services)\b"
    ],
    "farewell": [
        r"\b(bye|goodbye|see\s*you|thanks|thank\s*you|shukriya|dhanyawad)\b"
    ],
    "timing_inquiry": [
        r"\b(timing|timings|hours|open|close|closing|shut|khuli|band|kab\s*khulta|kab\s*khulegi)\b"
    ],
    "pricing_inquiry": [
        r"\b(price|pricing|rate|rates|cost|kitna|charges|fees|how\s*much|rate\s*card)\b"
    ],
    "service_inquiry": [
        r"\b(service|services|menu|offer|haircut|hair\s*cut|fade|beard|shave|facial|spa|color|treatment|bleach|cleaner)\b"
    ],
    "barber_inquiry": [
        r"\b(barber|barbers|stylist|stylists|specialist|who\s*works|experience|staff|choose\s*barber)\b"
    ],
    "availability_inquiry": [
        r"\b(available|availability|free|slot|slots|khali|empty)\b"
    ],
    "book_appointment": [
        r"\b(book|booking|appointment|reserve|slot|schedule|lena\s*hai|karwana\s*hai)\b"
    ],
    "cancel_appointment": [
        r"\b(cancel|cancellation|cancelling|hatao|nahi\s*aana)\b"
    ],
    "view_booking": [
        r"\b(status|my\s*booking|my\s*appointment|check\s*booking|check\s*status)\b"
    ],
    "lodge_complaint": [
        r"\b(complaint|complain|bad\s*service|cut\s*too\s*short|uneven|dirty|waited|angry|refund|irritated|worst)\b"
    ],
    "human_handover": [
        r"\b(manager|human|real\s*person|talk\s*to\s*someone|call\s*me|owner|staff|escalate)\b"
    ],
    "payment_inquiry": [
        r"\b(payment|pay|upi|gpay|google\s*pay|phonepe|paytm|cash|card|credit)\b"
    ],
    "parking_inquiry": [
        r"\b(parking|park|car|bike|two\s*wheeler|vehicle)\b"
    ],
    "hygiene_inquiry": [
        r"\b(hygiene|clean|cleanliness|sanitize|sterilize|blade|razor|disposable|feature|features)\b"
    ],
    "walkin_policy": [
        r"\b(walk\s*in|walkin|direct\s*aana|without\s*appointment)\b"
    ]
}

# Catalog Mapping for [S1] - [S16] Codes
CATALOG_CODE_MAP = {
    "s1": "Hair Cut",
    "s2": "Head Wash",
    "s3": "Head Shave",
    "s4": "Beard Trim / Gaming Shave",
    "s5": "Head Massage",
    "s6": "Head Massage Olive/Almond Oil",
    "s7": "Face Bleach",
    "s8": "D Tan Cleaner",
    "s9": "D Tan Facial",
    "s10": "Gold/Diamond Facial with Oxy Bleach",
    "s11": "Whitening Facial",
    "s12": "Keratin Hair Spa",
    "s13": "Loreal Matrix Hair Spa",
    "s14": "Hair Colour",
    "s15": "Hair Colour & Hair Cut",
    "s16": "Anti Dandruff Treatment (3 seatings)"
}

# Shortcuts Mapping for Quick Selection 1-7
MENU_CODE_MAP = {
    "1": "Hair Cut",
    "2": "Beard Trim / Gaming Shave",
    "3": "Hair Cut + Beard Trim / Gaming Shave",
    "4": "Head Wash",
    "5": "Keratin Hair Spa",
    "6": "D Tan Cleaner",
    "7": "Hair Colour"
}


def get_master_menu() -> str:
    """Returns the clean, modern interactive WhatsApp menu (big company card layout)."""
    return (
        f"💈 *{SALON_NAME}* (BH-5, LPU Campus) 💈\n"
        "✂️ _Official Campus Grooming Assistant_\n"
        "⏰ Open Daily: 09:00 AM – 09:00 PM\n\n"
        "Please select a service by number to book:\n\n"
        "1️⃣ *Hair Cut* — ₹100 _(20 min)_\n"
        "2️⃣ *Beard Trim / Shave* — ₹50 _(15 min)_\n"
        "3️⃣ *Cut + Beard Combo* — ₹140 _(30 min)_\n"
        "4️⃣ *Head Wash* — ₹50 _(15 min)_\n"
        "5️⃣ *Hair Spa / Keratin* — ₹400 _(45 min)_\n"
        "6️⃣ *D-Tan Cleaner / Facial* — ₹300 _(25 min)_\n"
        "7️⃣ *Hair Colour* — ₹450 _(40 min)_\n\n"
        "───────────────\n"
        "8️⃣ 📋 *Full Price List (All Services [S1-S16])*\n"
        "9️⃣ ⏰ *Salon Timings & Location*\n"
        "🔟 💬 *Check Booking / Cancel*\n"
        "1️⃣1️⃣ 🤝 *Talk to Salon Manager*\n\n"
        "💡 *Tips:*\n"
        "• Reply with a number (e.g. *1* or *3*)\n"
        "• Or select multiple (e.g. *1 and 2* or *S1 and S4*)\n"
        "• Or reply *8* for the complete rate card."
    )


def get_full_price_catalog() -> str:
    """Returns categorized full rate card with [S1] - [S16] codes."""
    return (
        f"💈 *{SALON_NAME.upper()} — COMPLETE RATE CARD* 💈\n"
        "📍 BH-5 Ground Floor, LPU Campus\n"
        "⏰ Open Daily: 09:00 AM – 09:00 PM\n\n"
        "✂️ *Hair & Styling Services:*\n"
        "• *[S1]* Hair Cut — ₹100 _(20m)_\n"
        "• *[S2]* Head Wash — ₹50 _(15m)_\n"
        "• *[S3]* Head Shave — ₹120 _(20m)_\n"
        "• *[S14]* Hair Colour — ₹450 _(40m)_\n"
        "• *[S15]* Hair Colour & Hair Cut Combo — ₹500 _(55m)_\n\n"
        "🧔 *Beard & Massage Services:*\n"
        "• *[S4]* Beard Trim / Gaming Shave — ₹50 _(15m)_\n"
        "• *[S5]* Head Massage — ₹100 _(20m)_\n"
        "• *[S6]* Head Massage Olive/Almond Oil — ₹150 _(25m)_\n\n"
        "✨ *Facials & Skin Care:*\n"
        "• *[S7]* Face Bleach — ₹180 _(20m)_\n"
        "• *[S8]* D-Tan Cleaner — ₹300 _(30m)_\n"
        "• *[S9]* D-Tan Facial — ₹450 _(40m)_\n"
        "• *[S10]* Gold/Diamond Facial + Oxy Bleach — ₹700 _(60m)_\n"
        "• *[S11]* Whitening Facial — ₹600 _(50m)_\n\n"
        "💆 *Hair Spa & Treatments:*\n"
        "• *[S12]* Keratin Hair Spa — ₹400 _(45m)_\n"
        "• *[S13]* Loreal Matrix Hair Spa — ₹500 _(45m)_\n"
        "• *[S16]* Anti Dandruff Treatment (3 seatings) — ₹1500 _(60m)_\n\n"
        "───────────────\n"
        "👉 *To book:* Reply with any code (e.g. *S1*, *S4*, *S1 and S4*) or number (*1-7*), or type *'menu'*."
    )


def extract_name_and_phone(text: str) -> tuple[str | None, str | None]:
    """Extracts customer name and 10-digit phone number from text."""
    clean_text = text.strip()
    phone = None
    name = None

    # Find 10-digit phone number
    phone_match = re.search(r"\b(?:\+91[-.\s]?)?([6789]\d{9})\b", clean_text)
    if phone_match:
        phone = phone_match.group(1)
        remainder = clean_text[:phone_match.start()] + " " + clean_text[phone_match.end():]
    else:
        digits = re.search(r"\b(\d{10})\b", clean_text)
        if digits:
            phone = digits.group(1)
            remainder = clean_text[:digits.start()] + " " + clean_text[digits.end():]
        else:
            remainder = clean_text

    # Clean remainder of common filler words to extract name
    remainder = re.sub(
        r"\b(my\s*name\s*is|name|i\s*am|this\s*is|for|contact|phone|number|mobile|no|call|me|mr|mrs|ms)\b",
        "", remainder, flags=re.IGNORECASE
    )
    candidate_name = re.sub(r"[^\w\s]", " ", remainder).strip()
    words = candidate_name.split()
    if words:
        clean_words = [
            w for w in words
            if w.isalpha() and w.lower() not in [
                "cancel", "book", "hi", "hello", "today", "tomorrow", "ok", "yes", "no", "status", "menu", "option"
            ]
        ]
        if clean_words:
            name = " ".join([w.capitalize() for w in clean_words[:3]])

    return name, phone


class RuleBasedSalonChatbot:
    """
    Deterministic Goal-Oriented Conversational Agent.
    Maintains slot-filling conversation state across turns.
    """
    DEFAULT_BARBER = "default"

    def __init__(self):
        self.state = "IDLE"
        self.slots = {
            "service": None,
            "barber": self.DEFAULT_BARBER,
            "date": None,
            "time_slot": None,
            "customer_name": None,
            "phone": None
        }
        self.active_intent = None

    def reset_state(self):
        self.state = "IDLE"
        self.slots = {
            "service": None,
            "barber": self.DEFAULT_BARBER,
            "date": None,
            "time_slot": None,
            "customer_name": None,
            "phone": None
        }
        self.active_intent = None

    def extract_entities(self, text: str) -> dict:
        """Extracts recognizable slots from customer query."""
        extracted = {}
        text_lower = text.lower()
        stripped = text_lower.strip().rstrip(".")

        # 1. Phone Number (10 digits)
        phone_match = re.search(r"\b(?:\+91[-.\s]?)?([6789]\d{9})\b", text)
        if phone_match:
            extracted["phone"] = phone_match.group(1)

        # 2. S-Code Catalog Recognition ([S1] to [S16])
        multi_s_match = re.search(r"\b[sS](\d{1,2})\s*(?:and|&|\+|\,)\s*[sS](\d{1,2})\b", text)
        if multi_s_match:
            code1 = f"s{multi_s_match.group(1)}"
            code2 = f"s{multi_s_match.group(2)}"
            name1 = CATALOG_CODE_MAP.get(code1)
            name2 = CATALOG_CODE_MAP.get(code2)
            if name1 and name2:
                if (code1 == "s1" and code2 == "s4") or (code1 == "s4" and code2 == "s1"):
                    extracted["service"] = "Hair Cut + Beard Trim / Gaming Shave"
                else:
                    extracted["service"] = f"{name1} + {name2}"
        else:
            single_s_match = re.search(r"\b[sS]([1-9]|1[0-6])\b", text)
            if single_s_match:
                code = f"s{single_s_match.group(1)}"
                if code in CATALOG_CODE_MAP:
                    extracted["service"] = CATALOG_CODE_MAP[code]

        # 3. Numeric Menu Shortcuts (1 to 7)
        if "service" not in extracted:
            # Multi-number check (e.g. "1 and 2", "1, 2", "1 + 2", "1 & 2")
            multi_num_match = re.search(r"\b([1-7])\s*(?:and|&|\+|\,)\s*([1-7])\b", text_lower)
            if multi_num_match:
                n1, n2 = multi_num_match.group(1), multi_num_match.group(2)
                s1 = MENU_CODE_MAP.get(n1)
                s2 = MENU_CODE_MAP.get(n2)
                if s1 and s2:
                    if (n1 == "1" and n2 == "2") or (n1 == "2" and n2 == "1"):
                        extracted["service"] = "Hair Cut + Beard Trim / Gaming Shave"
                    else:
                        extracted["service"] = f"{s1} + {s2}"

            # In AWAITING_DATE state: '1' is Today, '2' is Tomorrow. Numbers 3-7 mean user changed service!
            elif self.state == "AWAITING_DATE":
                if stripped in ["3", "4", "5", "6", "7"]:
                    extracted["service"] = MENU_CODE_MAP[stripped]

            # In AWAITING_TIME or AWAITING_PHONE/CONTACT: do not interpret bare single numbers as service
            elif not self.state.startswith("AWAITING_TIME") and not self.state.startswith("AWAITING_PHONE") and not self.state.startswith("AWAITING_NAME"):
                single_num_match = re.match(r"^\s*(?:option\s*)?([1-7])(?:\b|\.|\s|$)", text_lower)
                if single_num_match and not re.search(r"^\s*[1-7]\s*(?:am|pm|:)", text_lower):
                    num = single_num_match.group(1)
                    extracted["service"] = MENU_CODE_MAP[num]

        # 4. Service Keywords
        if "service" not in extracted and not self.state.startswith("AWAITING_TIME") and not self.state.startswith("AWAITING_PHONE"):
            found = []
            if re.search(r"\b(haircut|hair\s*cut|cut|baal)\b", text_lower) and not re.search(r"\b(colour|color)\s*&\s*(cut|hair\s*cut)\b", text_lower):
                found.append("Hair Cut")
            if re.search(r"\b(beard|darhi|gaming\s*shave)\b", text_lower):
                found.append("Beard Trim / Gaming Shave")
            elif re.search(r"\b(head\s*shave)\b", text_lower):
                found.append("Head Shave")
            elif re.search(r"\b(shave)\b", text_lower) and "Beard Trim / Gaming Shave" not in found:
                found.append("Beard Trim / Gaming Shave")

            if re.search(r"\b(head\s*wash|wash)\b", text_lower):
                found.append("Head Wash")
            if re.search(r"\b(head\s*massage|massage)\b", text_lower):
                if re.search(r"\b(olive|almond)\b", text_lower):
                    found.append("Head Massage Olive/Almond Oil")
                else:
                    found.append("Head Massage")
            if re.search(r"\b(keratin|keratin\s*spa)\b", text_lower):
                found.append("Keratin Hair Spa")
            elif re.search(r"\b(matrix|loreal)\b", text_lower):
                found.append("Loreal Matrix Hair Spa")
            if re.search(r"\b(d\s*tan\s*facial|detan\s*facial)\b", text_lower):
                found.append("D Tan Facial")
            elif re.search(r"\b(d\s*tan\s*cleaner|detan\s*cleaner|d\s*tan|detan)\b", text_lower):
                found.append("D Tan Cleaner")
            elif re.search(r"\b(face\s*bleach|bleach)\b", text_lower):
                found.append("Face Bleach")
            elif re.search(r"\b(gold|diamond|oxy\s*bleach)\b", text_lower):
                found.append("Gold/Diamond Facial with Oxy Bleach")
            elif re.search(r"\b(whitening)\b", text_lower):
                found.append("Whitening Facial")
            if re.search(r"\b(colour|color|dye)\b", text_lower):
                if re.search(r"\b(cut|hair\s*cut)\b", text_lower):
                    found = [f for f in found if f != "Hair Cut"]
                    found.append("Hair Colour & Hair Cut")
                else:
                    found.append("Hair Colour")
            if re.search(r"\b(dandruff|anti\s*dandruff)\b", text_lower):
                found.append("Anti Dandruff Treatment (3 seatings)")

            if len(found) > 1:
                unique_found = []
                for s in found:
                    if s not in unique_found:
                        unique_found.append(s)
                extracted["service"] = " + ".join(unique_found)
            elif len(found) == 1:
                extracted["service"] = found[0]

        # Fallback to direct DB lookup if still not found
        if "service" not in extracted and not self.state.startswith("AWAITING_TIME") and not self.state.startswith("AWAITING_PHONE"):
            for s in get_all_services():
                if s["name"].lower() in text_lower:
                    extracted["service"] = s["name"]
                    break

        # 5. Barber Extraction (Auto-assigned)
        extracted["barber"] = self.DEFAULT_BARBER

        # 6. Date Extraction
        today = datetime.now()
        if self.state == "AWAITING_DATE":
            if stripped in ["1", "today", "aaj"] or stripped.startswith("1 "):
                extracted["date"] = today.strftime("%Y-%m-%d")
            elif stripped in ["2", "tomorrow", "kal"] or stripped.startswith("2 "):
                extracted["date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        if "date" not in extracted:
            if re.search(r"\b(today|aaj)\b", text_lower):
                extracted["date"] = today.strftime("%Y-%m-%d")
            elif re.search(r"\b(tomorrow|kal)\b", text_lower):
                extracted["date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                date_match = re.search(r"\b(202\d-[01]\d-[0-3]\d)\b", text)
                if date_match:
                    extracted["date"] = date_match.group(1)

        # 7. Time Extraction
        time_match = re.search(r"\b(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)\s*(am|pm)?\b", text_lower)
        if not time_match:
            time_match = re.search(r"\b(?:at\s+)?([01]?\d|2[0-3])\s*(am|pm)\b", text_lower)
        if not time_match and (self.state == "AWAITING_TIME" or re.search(r"\bat\s+\d", text_lower)):
            time_match = re.search(r"\b(?:at\s+)?([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)?\b", text_lower)

        if time_match:
            hour_str = time_match.group(1)
            groups = time_match.groups()
            meridiem = None
            min_str = "00"
            for g in groups[1:]:
                if g in ["am", "pm"]:
                    meridiem = g
                elif g and g.isdigit():
                    min_str = g

            if not phone_match or time_match.start() < phone_match.start() or time_match.end() > phone_match.end():
                try:
                    hour = int(hour_str)
                    minute = int(min_str)
                    if meridiem:
                        if meridiem == "pm" and hour < 12:
                            hour += 12
                        elif meridiem == "am" and hour == 12:
                            hour = 0
                    elif self.state == "AWAITING_TIME":
                        # In salon context (09:00 - 21:00), 1..8 implies PM
                        if 1 <= hour <= 8:
                            hour += 12
                    if 9 <= hour <= 21:
                        extracted["time_slot"] = f"{hour:02d}:{minute:02d}"
                except ValueError:
                    pass

        # 8. Customer Name Extraction
        if self.state in ["AWAITING_NAME", "AWAITING_PHONE"]:
            parsed_name, parsed_phone = extract_name_and_phone(text)
            if parsed_name:
                extracted["customer_name"] = parsed_name
            if parsed_phone and "phone" not in extracted:
                extracted["phone"] = parsed_phone
        else:
            name_match = re.search(r"(?:for|name\s*is|i\s*am|this\s*is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
            if name_match:
                candidate = name_match.group(1)
                if "Staff" not in candidate and "Razors" not in candidate:
                    extracted["customer_name"] = candidate

        return extracted

    def detect_intent(self, text: str) -> tuple[str, float, list[str]]:
        """
        Classifies intent using regex pattern matches and numeric menu mapping.
        Returns: (intent_name, confidence_score, matched_patterns)
        """
        text_lower = text.lower()
        stripped = text_lower.strip().rstrip(".")
        matched_rules = []

        # Global Numeric Menu Selections (available everywhere)
        if stripped in ["8", "option 8", "catalog", "prices", "price list", "rate card", "ratecard"]:
            return "pricing_inquiry", 0.99, ["DIRECT_MENU_CHOICE_8"]
        elif stripped in ["9", "option 9", "timings", "timing", "location", "hours", "address"]:
            return "timing_inquiry", 0.99, ["DIRECT_MENU_CHOICE_9"]
        elif stripped in ["10", "option 10", "status", "check booking", "my booking"]:
            return "view_booking", 0.99, ["DIRECT_MENU_CHOICE_10"]
        elif stripped in ["11", "option 11", "manager", "staff", "human", "talk to human"]:
            return "human_handover", 0.99, ["DIRECT_MENU_CHOICE_11"]
        elif stripped in ["menu", "help", "options", "start", "home", "main menu"]:
            return "show_menu", 0.99, ["DIRECT_MENU_ROOT"]

        # If not active slot filling, 1-7 books directly
        if not self.state.startswith("AWAITING_"):
            if stripped in ["1", "option 1", "2", "option 2", "3", "option 3", "4", "option 4", "5", "option 5", "6", "option 6", "7", "option 7"]:
                return "book_appointment", 0.99, ["DIRECT_MENU_SERVICE_CHOICE"]

        best_intent = "unknown"
        for intent, patterns in INTENT_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text_lower):
                    matched_rules.append(f"RULE_{intent.upper()}: matched '{pat}'")
                    best_intent = intent
                    break
            if best_intent != "unknown":
                break

        confidence = 0.95 if best_intent != "unknown" else 0.20
        return best_intent, confidence, matched_rules

    def process_message(self, user_message: str) -> dict:
        """
        Main execution pipeline for Approach 1.
        Returns response dict with explainability trace.
        """
        trace = {
            "approach": "Rule-Based FSM (Approach 1)",
            "raw_input": user_message,
            "rules_fired": [],
            "state_before": self.state,
            "slots_before": dict(self.slots),
            "state_after": None,
            "slots_after": None,
            "sql_queries": []
        }

        user_msg_clean = user_message.strip().lower()

        # ── 1. GLOBAL ESCAPES (Callable from ANY state) ──
        if user_msg_clean in ["menu", "help", "options", "start", "main menu", "home"]:
            self.reset_state()
            return {
                "response": get_master_menu(),
                "detected_intent": "show_menu",
                "confidence": 1.0,
                "trace": trace
            }

        if user_msg_clean in ["8", "option 8", "catalog", "prices", "price list", "rate card", "ratecard"]:
            self.reset_state()
            return {
                "response": get_full_price_catalog(),
                "detected_intent": "pricing_inquiry",
                "confidence": 1.0,
                "trace": trace
            }

        if user_msg_clean in ["9", "option 9", "timings", "timing", "hours", "location", "address"]:
            self.reset_state()
            return {
                "response": f"⏰ *{SALON_NAME} Timings & Location:*\n• {OPERATING_HOURS}\n• Location: {ADDRESS}\n\n👉 Reply *'menu'* for options or *1-7* to book a slot!",
                "detected_intent": "timing_inquiry",
                "confidence": 1.0,
                "trace": trace
            }

        if user_msg_clean in ["10", "option 10", "status", "check booking", "my booking"]:
            self.reset_state()
            self.state = "AWAITING_STATUS_PHONE"
            return {
                "response": "📋 *Check Booking / Status:*\nPlease enter your 10-digit mobile number to look up your appointments:",
                "detected_intent": "view_booking",
                "confidence": 1.0,
                "trace": trace
            }

        if user_msg_clean in ["11", "option 11", "manager", "staff", "human", "talk to human"]:
            self.reset_state()
            add_to_handover_queue("Customer", user_message, reason="User requested manager/staff")
            trace["sql_queries"].append("INSERT INTO handover_queue")
            return {
                "response": f"🤝 I have notified the salon staff at {SALON_NAME}. You can also call or WhatsApp our desk directly at *{PHONE_WHATSAPP}*.",
                "detected_intent": "human_handover",
                "confidence": 1.0,
                "trace": trace
            }

        if user_msg_clean in ["cancel", "stop", "reset", "exit", "quit"]:
            if self.state.startswith("AWAITING_"):
                self.reset_state()
                return {
                    "response": f"Current action cancelled. How else can I assist you at {SALON_NAME}? Reply *'menu'* to see options.",
                    "detected_intent": "cancel_appointment",
                    "confidence": 1.0,
                    "trace": trace
                }
            else:
                self.reset_state()
                self.state = "AWAITING_CANCEL_PHONE"
                return {
                    "response": "To cancel your appointment, please provide your 10-digit registered mobile number (e.g. *9876543210*):",
                    "detected_intent": "cancel_appointment",
                    "confidence": 1.0,
                    "trace": trace
                }

        # ── 2. DEDICATED STATUS LOOKUP HANDLER ──
        if self.state == "AWAITING_STATUS_PHONE":
            extracted_slots = self.extract_entities(user_message)
            phone = extracted_slots.get("phone")
            if not phone:
                clean_digits = re.sub(r"\D", "", user_message)
                if len(clean_digits) >= 10:
                    phone = clean_digits[-10:]

            if phone:
                bookings = get_appointments_by_phone(phone)
                trace["sql_queries"].append(f"SELECT * FROM appointments WHERE phone='{phone}'")
                if bookings:
                    lines = [f"📋 *Found {len(bookings)} Appointment(s) for {phone}:*"]
                    for b in bookings:
                        status_emoji = "✅" if b.get('status') == 'BOOKED' else "❌"
                        lines.append(
                            f"\n{status_emoji} *Booking #{b['id']}*\n"
                            f"• *Service:* {b.get('service_name', 'Salon Service')}\n"
                            f"• *Date & Time:* {b.get('appointment_date')} at {b.get('start_time')}\n"
                            f"• *Status:* *{b.get('status', 'BOOKED')}*\n"
                            f"• *Client:* {b.get('customer_name', 'Customer')}"
                        )
                    lines.append("\n💡 Reply *'cancel'* if you need to cancel this booking, or *'menu'* for options.")
                    response_text = "\n".join(lines)
                else:
                    response_text = (
                        f"🔍 No active appointments found for phone ending in *{phone[-4:]}*.\n\n"
                        f"Would you like to book a new appointment? Reply with *1-7* or type *'menu'*."
                    )
                self.reset_state()
            else:
                response_text = "Please enter a valid 10-digit mobile number (e.g. *9876543210*) to check your appointment status:"

            trace["state_after"] = self.state
            trace["slots_after"] = dict(self.slots)
            return {
                "response": response_text,
                "detected_intent": "view_booking",
                "confidence": 1.0,
                "trace": trace
            }

        # ── 3. INTENT DETECTION & ENTITY EXTRACTION ──
        intent, conf, rules = self.detect_intent(user_message)
        trace["rules_fired"].extend(rules)
        trace["detected_intent"] = intent
        trace["confidence"] = conf

        new_slots = self.extract_entities(user_message)

        # Fresh booking initiation: if user explicitly says "can i book an appointment", "book appointment", etc.
        # without specifying a service in this message, ALWAYS reset state and show the service menu fresh!
        if intent == "book_appointment" and not new_slots.get("service"):
            self.reset_state()
            self.state = "AWAITING_SERVICE"
            response_text = (
                "Sure! Which service would you like to book?\n\n"
                "1️⃣ *Hair Cut* — ₹100\n"
                "2️⃣ *Beard Trim / Shave* — ₹50\n"
                "3️⃣ *Cut + Beard Combo* — ₹140\n"
                "4️⃣ *Head Wash* — ₹50\n"
                "5️⃣ *Keratin Spa* — ₹400\n"
                "6️⃣ *D-Tan Cleaner* — ₹300\n"
                "7️⃣ *Hair Colour* — ₹450\n\n"
                "───────────────\n"
                "8️⃣ 📋 *Full Price List (All Services [S1-S16])*\n\n"
                "💡 _Reply with a number (1-7), code (S1-S16), or service name!_"
            )
            trace["state_after"] = self.state
            trace["slots_after"] = dict(self.slots)
            return {
                "response": response_text,
                "detected_intent": intent,
                "confidence": conf,
                "trace": trace
            }

        # If user initiates a new booking AND specifies a service in this message (e.g. "book haircut tomorrow"):
        if intent == "book_appointment" and new_slots.get("service") and self.state == "IDLE":
            self.reset_state()
            self.slots["service"] = new_slots["service"]
            self.slots["date"] = new_slots.get("date")
            self.slots["time_slot"] = new_slots.get("time_slot")
            self.slots["customer_name"] = new_slots.get("customer_name")
            self.slots["phone"] = new_slots.get("phone")

        # Service switching support: if user in slot filling chooses a new service, update and restart flow
        elif new_slots.get("service") and self.state.startswith("AWAITING_") and self.state != "AWAITING_SERVICE":
            if new_slots["service"] != self.slots.get("service"):
                self.slots["service"] = new_slots["service"]
                self.slots["date"] = None
                self.slots["time_slot"] = None
                self.state = "AWAITING_DATE"
                trace["rules_fired"].append(f"SWITCHED_SERVICE: {new_slots['service']}")

        for k, v in new_slots.items():
            if v and not self.slots.get(k):
                self.slots[k] = v
                trace["rules_fired"].append(f"EXTRACTED_SLOT: {k} = '{v}'")

        # If user selected a service while in IDLE, start booking immediately
        if self.state == "IDLE" and self.slots.get("service") and intent not in [
            "pricing_inquiry", "timing_inquiry", "human_handover", "lodge_complaint", "cancel_appointment"
        ]:
            intent = "book_appointment"

        # ── 4. FSM EXECUTION ──
        response_text = ""

        # Immediate escalation
        if intent == "human_handover":
            self.reset_state()
            phone = self.slots.get("phone") or "Customer"
            add_to_handover_queue(phone, user_message, reason="User requested human staff")
            trace["sql_queries"].append("INSERT INTO handover_queue")
            response_text = f"🤝 I have notified the staff at {SALON_NAME}. You can also reach our desk directly via call or WhatsApp at {PHONE_WHATSAPP}."
            self.state = "IDLE"

        # Complaints
        elif intent == "lodge_complaint":
            self.reset_state()
            name = self.slots.get("customer_name") or "Valued Customer"
            phone = self.slots.get("phone") or "Pending"
            cid = log_complaint(name, phone, user_message, severity="HIGH")
            trace["sql_queries"].append(f"INSERT INTO complaints (ID={cid})")
            response_text = f"🙏 We sincerely apologize for your experience. Your complaint has been registered as Ticket #{cid}. Our salon manager reviews every issue and will address this immediately."
            self.state = "IDLE"

        # Cancellation
        elif intent == "cancel_appointment":
            phone = self.slots.get("phone")
            if not phone:
                response_text = "To cancel your appointment, please provide your 10-digit registered phone number (e.g., 'Cancel booking for 6284421638')."
                self.state = "AWAITING_CANCEL_PHONE"
            else:
                success, msg = cancel_appointment_by_phone(phone)
                trace["sql_queries"].append(f"UPDATE appointments SET status='CANCELLED' WHERE phone='{phone}'")
                response_text = msg
                self.reset_state()

        elif self.state == "AWAITING_CANCEL_PHONE":
            phone = self.slots.get("phone")
            if phone:
                success, msg = cancel_appointment_by_phone(phone)
                trace["sql_queries"].append(f"UPDATE appointments SET status='CANCELLED' WHERE phone='{phone}'")
                response_text = msg
                self.reset_state()
            else:
                response_text = "Please enter a valid 10-digit mobile number to locate and cancel your reservation."

        # Active Slot-Filling State Progression
        elif self.state.startswith("AWAITING_"):
            response_text = self._handle_slot_filling(trace)

        # Check booking status intent
        elif intent == "view_booking":
            phone = self.slots.get("phone")
            if not phone:
                response_text = "📋 *Check Booking / Status:*\nPlease enter your 10-digit mobile number to look up your appointments:"
                self.state = "AWAITING_STATUS_PHONE"
            else:
                bookings = get_appointments_by_phone(phone)
                trace["sql_queries"].append(f"SELECT * FROM appointments WHERE phone='{phone}'")
                if bookings:
                    b = bookings[0]
                    response_text = f"📋 Booking Found: #{b['id']} for {b['service_name']} on {b['appointment_date']} at {b['start_time']}. Status: **{b['status']}**."
                else:
                    response_text = f"No active appointments found for phone ending in {phone[-4:]}."
                self.reset_state()

        # Pricing Queries
        elif intent == "pricing_inquiry":
            service_kw = self.slots.get("service")
            if service_kw:
                s_obj = get_service_by_name_or_id(service_kw)
                if s_obj:
                    response_text = f"💰 *{s_obj['name']}* is priced at *₹{int(s_obj['price_inr'])}* ({s_obj['duration_minutes']} mins). Reply *'book {s_obj['name']}'* to reserve a slot!"
                else:
                    response_text = "At Razors-n-scissors, Hair Cut is ₹100, Beard Trim is ₹50, and Head Wash is ₹50. Reply *8* to see the full rate card."
            else:
                response_text = get_full_price_catalog()

        elif intent == "timing_inquiry":
            response_text = f"⏰ **{SALON_NAME} Timings:**\n• {OPERATING_HOURS}\n• Location: {ADDRESS}\nWould you like to reserve a time slot today?"

        elif intent == "barber_inquiry":
            response_text = (
                f"✂️ **{SALON_NAME} Styling Staff:**\n"
                "All services are handled by our professionally trained styling staff with strict hygiene standards. "
                "You do not need to choose a specific barber — our expert staff will attend to you promptly!"
            )

        elif intent == "service_inquiry":
            response_text = get_master_menu()

        elif intent == "payment_inquiry":
            response_text = "💳 We accept Cash and all UPI apps (Google Pay, PhonePe, Paytm). No extra transaction fees."

        elif intent == "parking_inquiry":
            response_text = f"🅿️ Ample parking is conveniently available near {ADDRESS} on campus."

        elif intent == "hygiene_inquiry":
            response_text = (
                "🧼 **Salient Features of Razors-n-scissors:**\n"
                "1. Maintenance of hygiene (sterilized shears, fresh blades, fresh towels)\n"
                "2. Professionally trained staff\n"
                "3. Pocket friendly rates"
            )

        elif intent == "walkin_policy":
            response_text = "🚶 Walk-ins are always welcome! However, appointments booked here are given priority so you skip the queue."

        elif intent in ["greeting", "show_menu"]:
            self.reset_state()
            response_text = get_master_menu()

        elif intent == "farewell":
            response_text = f"Thank you for contacting {SALON_NAME}! Groom yourself at Razors-n-scissors. Have a great day! ✂️"

        # Booking Flow Handling
        elif intent == "book_appointment":
            response_text = self._handle_slot_filling(trace)

        else:
            response_text = "I'm not completely sure I understood that. You can ask about haircut prices, our timings at BH-5, or reply with a number (1-7) to book an appointment."
            self.state = "IDLE"

        trace["state_after"] = self.state
        trace["slots_after"] = dict(self.slots)

        return {
            "response": response_text,
            "detected_intent": intent,
            "confidence": conf,
            "trace": trace
        }

    def _handle_slot_filling(self, trace: dict) -> str:
        """
        Executes slot-filling dialog progression:
        1. Service -> 2. Day Selection -> 3. Available Time Slot -> 4 & 5. Contact (Name & Phone)
        """
        # Ensure barber slot is auto-populated
        if not self.slots.get("barber"):
            self.slots["barber"] = self.DEFAULT_BARBER

        # Slot 1: Service
        if not self.slots["service"]:
            self.state = "AWAITING_SERVICE"
            return (
                "Sure! Which service would you like to book?\n\n"
                "1️⃣ *Hair Cut* — ₹100\n"
                "2️⃣ *Beard Trim / Shave* — ₹50\n"
                "3️⃣ *Cut + Beard Combo* — ₹140\n"
                "4️⃣ *Head Wash* — ₹50\n"
                "5️⃣ *Keratin Spa* — ₹400\n"
                "6️⃣ *D-Tan Cleaner* — ₹300\n"
                "7️⃣ *Hair Colour* — ₹450\n\n"
                "💡 _Reply with a number (1-7) or full code from catalog (S1-S16)_"
            )

        # Slot 2: Date (Day Selection)
        if not self.slots["date"]:
            self.state = "AWAITING_DATE"
            s_obj = get_service_by_name_or_id(self.slots["service"])
            price_info = f" (₹{int(s_obj['price_inr'])})" if s_obj else ""
            dur_info = f" · {s_obj['duration_minutes']} mins" if s_obj else ""

            today = datetime.now()
            today_date_str = today.strftime("%Y-%m-%d")
            today_str = today.strftime("%a, %b %d")
            tomorrow = today + timedelta(days=1)
            tomorrow_date_str = tomorrow.strftime("%Y-%m-%d")
            tomorrow_str = tomorrow.strftime("%a, %b %d")

            from database.db import is_salon_closed
            today_closed, today_reason = is_salon_closed(today_date_str)
            tomorrow_closed, tomorrow_reason = is_salon_closed(tomorrow_date_str)

            today_line = f"1️⃣ *Today* ({today_str}) 🔴 _[Closed: {today_reason}]_" if today_closed else f"1️⃣ *Today* ({today_str})"
            tomorrow_line = f"2️⃣ *Tomorrow* ({tomorrow_str}) 🔴 _[Closed: {tomorrow_reason}]_" if tomorrow_closed else f"2️⃣ *Tomorrow* ({tomorrow_str})"

            return (
                f"Selected: ✂️ *{self.slots['service']}*{price_info}{dur_info}\n\n"
                "📅 *Which day would you like to visit?*\n"
                f"{today_line}\n"
                f"{tomorrow_line}\n\n"
                "💡 _Reply *1* for Today, *2* for Tomorrow, or type any date (YYYY-MM-DD)_"
            )

        # Slot 3: Time Slot (Show real available slots for that date)
        if not self.slots["time_slot"]:
            self.state = "AWAITING_TIME"
            date_str = self.slots["date"]

            from database.db import is_salon_closed
            closed, reason = is_salon_closed(date_str)
            if closed:
                self.slots["date"] = None
                return (
                    f"⚠️ *Razors-n-scissors is closed on {date_str}* ({reason}).\n\n"
                    f"No appointments can be scheduled on this day.\n"
                    f"Please choose another date (reply *2* for tomorrow or type a date):"
                )

            slots = get_available_slots("default", date_str)

            # If booking for today, filter out passed hours
            now = datetime.now()
            if date_str == now.strftime("%Y-%m-%d"):
                cur_time = now.strftime("%H:%M")
                slots = [s for s in slots if s > cur_time]

            if not slots:
                return (
                    f"⚠️ No remaining slots available on {date_str}.\n"
                    f"Please choose another date (reply *2* for tomorrow or enter a date):"
                )

            # Format into Morning, Afternoon, Evening groups
            morning = [s for s in slots if s < "12:00"]
            afternoon = [s for s in slots if "12:00" <= s < "16:00"]
            evening = [s for s in slots if s >= "16:00"]

            def fmt_12h(s):
                try:
                    return datetime.strptime(s, "%H:%M").strftime("%I:%M %p").lstrip("0")
                except Exception:
                    return s

            lines = [
                f"📅 *Date Selected:* {date_str}\n",
                "⏰ *Please select your preferred time slot:*\n"
            ]

            if morning:
                lines.append(f"🌅 *Morning:*\n• " + "  •  ".join([fmt_12h(s) for s in morning[:6]]))
            if afternoon:
                lines.append(f"☀️ *Afternoon:*\n• " + "  •  ".join([fmt_12h(s) for s in afternoon[:6]]))
            if evening:
                lines.append(f"🌆 *Evening:*\n• " + "  •  ".join([fmt_12h(s) for s in evening[:6]]))

            lines.append("\n💡 _Reply with your preferred time (e.g. *4pm*, *11:00 AM*, or *5:30pm*)_")
            return "\n".join(lines)

        # Slot 4 & 5: Customer Name and Phone Number (Prompt together)
        if not self.slots["customer_name"] and not self.slots["phone"]:
            self.state = "AWAITING_NAME"
            return (
                f"✂️ *Booking Details:*\n"
                f"• *Service:* {self.slots['service']}\n"
                f"• *When:* {self.slots['date']} at {self.slots['time_slot']}\n\n"
                f"👤 *Almost Done!*\n"
                f"Please provide your *Name* and *10-digit Mobile Number* to confirm:\n"
                f"_(e.g. *Suman 9876543210*)_"
            )

        if not self.slots["customer_name"]:
            self.state = "AWAITING_NAME"
            return "May I have your name for the reservation?"

        if not self.slots["phone"]:
            self.state = "AWAITING_PHONE"
            return f"Thanks {self.slots['customer_name']}! Please provide your 10-digit mobile number so we can confirm your booking."

        # All slots collected! Execute booking in database
        b_name = self.slots["barber"]
        s_name = self.slots["service"]
        dt = self.slots["date"]
        tm = self.slots["time_slot"]
        c_name = self.slots["customer_name"]
        ph = self.slots["phone"]

        success, msg, app_id = book_appointment(c_name, ph, s_name, b_name, dt, tm)
        trace["sql_queries"].append(f"INSERT INTO appointments ({c_name}, {ph}, {s_name}, {b_name}, {dt}, {tm}) -> ID: {app_id}")

        self.reset_state()
        if success:
            return (
                f"🎉 **Booking Confirmed at {SALON_NAME}!**\n\n"
                f"• **Appointment ID:** #{app_id}\n"
                f"• **Client:** {c_name}\n"
                f"• **Service:** {s_name}\n"
                f"• **When:** {dt} at {tm}\n"
                f"• **Contact:** {ph}\n"
                f"• **Location:** {ADDRESS}\n\n"
                f"We look forward to welcoming you! For enquiries or cancellation, reply *'10'* or call/WhatsApp {PHONE_WHATSAPP}. ✂️"
            )
        else:
            return f"⚠️ {msg}\nWould you like to try another time slot?"
