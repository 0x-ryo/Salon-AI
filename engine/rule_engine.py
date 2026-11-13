"""
Approach 1: Classical Rule-Based AI Engine & Finite State Machine (FSM).
Razors-n-scissors Salon (INT428 Project 13)
Implements:
1. Regex & Keyword Pattern Matchers for Intent Classification
2. Slot-Filling Dialogue State Tracker (Service, Date, Time, Phone, Name)
   - Barber choice removed; auto-assigned to salon styling staff
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
        PHONE_WHATSAPP = "+91 9877175449"
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
        r"\b(timing|timings|hours|open|close|closing|shut|khuli|band|kab\s*khulta)\b"
    ],
    "pricing_inquiry": [
        r"\b(price|pricing|rate|rates|cost|kitna|charges|fees|how\s*much)\b"
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
        r"\b(status|my\s*booking|my\s*appointment|check\s*booking)\b"
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
        "8️⃣ 📋 *Full Price List (All Services)*\n"
        "9️⃣ ⏰ *Salon Timings & Location*\n"
        "🔟 💬 *Check Booking / Cancel / Staff*\n\n"
        "💡 *Tips:*\n"
        "• Reply with a number (e.g. *1* or *3*)\n"
        "• Or select multiple (e.g. *1 and 2*)\n"
        "• Or type naturally: _'1 tomorrow at 4pm'_"
    )


class RuleBasedSalonChatbot:
    """
    Deterministic Goal-Oriented Conversational Agent.
    Maintains slot-filling conversation state across turns.
    """
    DEFAULT_BARBER = "Razors-n-scissors Staff"

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

        # 1. Phone Number (10 digits)
        phone_match = re.search(r"\b(?:\+91[-.\s]?)?([6789]\d{9})\b", text)
        if phone_match:
            extracted["phone"] = phone_match.group(1)

        # 2. Service Extraction with Multi-Service & Numeric Code Support
        MENU_CODE_MAP = {
            "1": "Hair Cut",
            "2": "Beard Trim / Gaming Shave",
            "3": "Hair Cut + Beard Trim / Gaming Shave",
            "4": "Head Wash",
            "5": "Keratin Hair Spa",
            "6": "D Tan Cleaner",
            "7": "Hair Colour"
        }

        # Multi-service check with numbers (e.g. "1 and 2", "1, 2", "1 + 2", "1 & 2")
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

        # If not numeric combo, check if message is a single number or starts with single number (e.g. "1", "1 tomorrow", "1 at 4pm")
        if "service" not in extracted and not self.state.startswith("AWAITING_TIME") and not self.state.startswith("AWAITING_PHONE"):
            single_num_match = re.match(r"^\s*(?:option\s*)?([1-7])(?:\b|\.|\s|$)", text_lower)
            if single_num_match and not re.search(r"^\s*[1-7]\s*(?:am|pm|:)", text_lower):
                num = single_num_match.group(1)
                extracted["service"] = MENU_CODE_MAP[num]

        # Multi-service & single service detection by keywords
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
                # Deduplicate
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

        # 3. Barber Extraction (Auto-assigned)
        extracted["barber"] = self.DEFAULT_BARBER

        # 4. Date Extraction (today, tomorrow, or YYYY-MM-DD)
        today = datetime.now()
        if re.search(r"\b(today|aaj)\b", text_lower):
            extracted["date"] = today.strftime("%Y-%m-%d")
        elif re.search(r"\b(tomorrow|kal)\b", text_lower):
            extracted["date"] = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_match = re.search(r"\b(202\d-[01]\d-[0-3]\d)\b", text)
            if date_match:
                extracted["date"] = date_match.group(1)

        # 5. Time Extraction
        # Look for explicit times with colon or am/pm first to avoid misinterpreting service digits
        time_match = re.search(r"\b(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)\s*(am|pm)?\b", text_lower)
        if not time_match:
            time_match = re.search(r"\b(?:at\s+)?([01]?\d|2[0-3])\s*(am|pm)\b", text_lower)
        if not time_match and (self.state == "AWAITING_TIME" or re.search(r"\bat\s+\d", text_lower)):
            time_match = re.search(r"\b(?:at\s+)?([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)?\b", text_lower)

        if time_match:
            hour_str = time_match.group(1)
            # Find minute and meridiem across groups
            groups = time_match.groups()
            meridiem = None
            min_str = "00"
            for g in groups[1:]:
                if g in ["am", "pm"]:
                    meridiem = g
                elif g and g.isdigit():
                    min_str = g

            # Avoid mistaking phone start as time
            if not phone_match or time_match.start() < phone_match.start() or time_match.end() > phone_match.end():
                try:
                    hour = int(hour_str)
                    minute = int(min_str)
                    if meridiem:
                        if meridiem == "pm" and hour < 12:
                            hour += 12
                        elif meridiem == "am" and hour == 12:
                            hour = 0
                    if 8 <= hour <= 21:  # Operating range
                        extracted["time_slot"] = f"{hour:02d}:{minute:02d}"
                except ValueError:
                    pass

        # 6. Customer Name Extraction
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

        # Direct Numeric Menu Selection (only if not in active slot filling)
        if not self.state.startswith("AWAITING_"):
            if stripped in ["1", "option 1", "2", "option 2", "3", "option 3", "4", "option 4", "5", "option 5", "6", "option 6", "7", "option 7"]:
                return "book_appointment", 0.99, ["DIRECT_MENU_SERVICE_CHOICE"]
            elif stripped in ["8", "option 8", "catalog", "prices", "price list"]:
                return "pricing_inquiry", 0.99, ["DIRECT_MENU_CHOICE_8"]
            elif stripped in ["9", "option 9", "timings", "timing", "location", "hours"]:
                return "timing_inquiry", 0.99, ["DIRECT_MENU_CHOICE_9"]
            elif stripped in ["10", "option 10", "status", "cancel", "my booking"]:
                return "view_booking", 0.99, ["DIRECT_MENU_CHOICE_10"]
            elif stripped in ["11", "option 11", "manager", "staff"]:
                return "human_handover", 0.99, ["DIRECT_MENU_CHOICE_11"]
            elif stripped in ["menu", "help", "options", "start"]:
                return "show_menu", 0.99, ["DIRECT_MENU_ROOT"]

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

        # 1. Intent Detection
        intent, conf, rules = self.detect_intent(user_message)
        trace["rules_fired"].extend(rules)
        trace["detected_intent"] = intent
        trace["confidence"] = conf

        # 2. Extract Entities
        new_slots = self.extract_entities(user_message)
        for k, v in new_slots.items():
            if v and not self.slots.get(k):
                self.slots[k] = v
                trace["rules_fired"].append(f"EXTRACTED_SLOT: {k} = '{v}'")

        # If user selected a service while in IDLE, start booking immediately
        if self.state == "IDLE" and self.slots.get("service") and intent not in [
            "pricing_inquiry", "timing_inquiry", "human_handover", "lodge_complaint", "cancel_appointment"
        ]:
            intent = "book_appointment"

        # 3. FSM Execution
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

        # Cancellation while in active slot filling
        elif self.state.startswith("AWAITING_") and (user_message.lower().strip() in ["cancel", "stop", "reset", "exit"] or intent == "farewell"):
            self.reset_state()
            response_text = "Booking process cancelled. How else can I assist you at Razors-n-scissors?"

        # Cancellation
        elif intent == "cancel_appointment":
            phone = self.slots.get("phone")
            if not phone:
                response_text = "To cancel your appointment, please provide your 10-digit registered phone number (e.g., 'Cancel booking for 9877175449')."
                self.state = "AWAITING_CANCEL_PHONE"
            else:
                success, msg = cancel_appointment_by_phone(phone)
                trace["sql_queries"].append(f"UPDATE appointments SET status='CANCELLED' WHERE phone='{phone}'")
                response_text = msg
                self.reset_state()

        # Cancellation phone state
        elif self.state == "AWAITING_CANCEL_PHONE":
            phone = self.slots.get("phone")
            if phone:
                success, msg = cancel_appointment_by_phone(phone)
                trace["sql_queries"].append(f"UPDATE appointments SET status='CANCELLED' WHERE phone='{phone}'")
                response_text = msg
                self.reset_state()
            else:
                response_text = "Please enter a valid 10-digit mobile number to locate and cancel your reservation."

        # Active Slot-Filling State Progression (Takes priority over general informational queries during active booking)
        elif self.state.startswith("AWAITING_") and not self.state.startswith("AWAITING_STATUS"):
            response_text = self._handle_slot_filling(trace)

        # Check booking status
        elif intent == "view_booking":
            phone = self.slots.get("phone")
            if not phone:
                response_text = "Please share your 10-digit phone number so I can check your appointment status."
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

        # Service / Pricing Queries
        elif intent == "pricing_inquiry":
            service_kw = self.slots.get("service")
            if service_kw:
                s_obj = get_service_by_name_or_id(service_kw)
                if s_obj:
                    response_text = f"💰 *{s_obj['name']}* is priced at *₹{int(s_obj['price_inr'])}* ({s_obj['duration_minutes']} mins). Reply *'book {s_obj['name']}'* to reserve a slot!"
                else:
                    response_text = "At Razors-n-scissors, Hair Cut is ₹100, Beard Trim is ₹50, and Head Wash is ₹50. Say 'services' to see the full list."
            else:
                services = get_all_services()
                lines = [
                    f"💈 *{SALON_NAME.upper()} — COMPLETE PRICE LIST*",
                    "📍 BH-5 Ground Floor, LPU Campus\n"
                ]
                for s in services:
                    lines.append(f"• *{s['name']}* — ₹{int(s['price_inr'])} _({s['duration_minutes']}m)_")
                lines.append("\n👉 Reply with a service number (1-7) or name to book directly!")
                response_text = "\n".join(lines)

        elif intent == "timing_inquiry":
            response_text = f"⏰ **{SALON_NAME} Timings:**\n• {OPERATING_HOURS}\n• Location: {ADDRESS}\nWould you like to reserve a time slot today?"

        elif intent == "barber_inquiry":
            response_text = (
                f"✂️ **{SALON_NAME} Styling Staff:**\n"
                "All services are handled by our professionally trained styling staff with strict hygiene standards. "
                "You do not need to choose a specific barber — our expert staff will attend to you promptly!"
            )

        elif intent == "service_inquiry":
            services = get_all_services()
            lines = [f"💈 **{SALON_NAME} Service Menu:**"]
            for s in services:
                lines.append(f"• **{s['name']}** — ₹{int(s['price_inr'])} ({s['duration_minutes']} mins)")
            lines.append("\nWhich service would you like to schedule?")
            response_text = "\n".join(lines)

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
            response_text = get_master_menu()

        elif intent == "farewell":
            response_text = f"Thank you for contacting {SALON_NAME}! Groom yourself at Razors-n-scissors. Have a great day! ✂️"

        # Booking Flow Handling (Slot Filling State Machine without Barber Choice)
        elif intent == "book_appointment" or self.state.startswith("AWAITING_"):
            response_text = self._handle_slot_filling(trace)

        else:
            response_text = "I'm not completely sure I understood that. You can ask about haircut prices, our timings at BH-5, or say 'Book appointment' to reserve a slot."
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
        Executes slot-filling dialog progression.
        Slots required: 1. Service -> 2. Date -> 3. Time -> 4. Customer Name -> 5. Phone
        (Barber choice removed - auto-assigned to salon styling staff)
        """
        # Ensure barber slot is auto-populated
        if not self.slots.get("barber"):
            self.slots["barber"] = self.DEFAULT_BARBER

        # Slot 1: Service
        if not self.slots["service"]:
            self.state = "AWAITING_SERVICE"
            return (
                "Sure! Which service would you like to book?\n"
                "(Options: 1️⃣ Hair Cut [₹100], 2️⃣ Beard Trim [₹50], 3️⃣ Combo [₹140], "
                "4️⃣ Head Wash [₹50], 5️⃣ Keratin Spa [₹400], 6️⃣ D-Tan [₹300], etc.)"
            )

        # Slot 2: Date
        if not self.slots["date"]:
            self.state = "AWAITING_DATE"
            s_obj = get_service_by_name_or_id(self.slots["service"])
            price_info = f" (₹{int(s_obj['price_inr'])})" if s_obj else ""
            dur_info = f" · {s_obj['duration_minutes']} mins" if s_obj else ""
            return (
                f"Selected: ✂️ *{self.slots['service']}*{price_info}{dur_info}\n\n"
                "What date and time would you like to visit?\n"
                "• Reply *'today at 4pm'*\n"
                "• Or *'tomorrow at 11am'*\n"
                "• Or any date like *2026-11-15*"
            )

        # Slot 3: Time
        if not self.slots["time_slot"]:
            self.state = "AWAITING_TIME"
            slots = get_available_slots("B1", self.slots["date"])[:6]
            slot_str = ", ".join(slots) if slots else "09:00, 10:00, 11:00, 14:00, 16:00, 18:00"
            return f"Available slots on {self.slots['date']}: {slot_str}. What time suits you?"

        # Slot 4: Customer Name
        if not self.slots["customer_name"]:
            self.state = "AWAITING_NAME"
            return "May I have your name for the reservation?"

        # Slot 5: Phone Number
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
                f"We look forward to welcoming you! For enquiries or changes, call/WhatsApp {PHONE_WHATSAPP}. ✂️"
            )
        else:
            return f"⚠️ {msg}\nWould you like to try another time slot?"
