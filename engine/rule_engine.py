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
    get_all_services, get_all_barbers, get_available_slots,
    book_appointment, cancel_appointment_by_phone, get_appointments_by_phone,
    log_complaint, add_to_handover_queue
)
from app.config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS

# Intent Regular Expression Catalog
INTENT_PATTERNS = {
    "greeting": [
        r"\b(hi|hello|hey|good\s*(morning|afternoon|evening)|namaste|salaam)\b"
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

        # 2. Service Extraction (matches real Razors-n-scissors service names)
        services = get_all_services()
        for s in services:
            s_name_lower = s["name"].lower()
            if s_name_lower in text_lower:
                extracted["service"] = s["name"]
                break

        if "service" not in extracted:
            if re.search(r"\b(hair\s*cut\s*&\s*hair\s*cut|colour\s*&\s*cut|color\s*&\s*cut|hair\s*color\s*&\s*cut)\b", text_lower):
                extracted["service"] = "Hair Colour & Hair Cut"
            elif re.search(r"\b(dandruff|anti\s*dandruff)\b", text_lower):
                extracted["service"] = "Anti Dandruff Treatment (3 seatings)"
            elif re.search(r"\b(gold|diamond|oxy\s*bleach)\b", text_lower):
                extracted["service"] = "Gold/Diamond Facial with Oxy Bleach"
            elif re.search(r"\b(whitening\s*facial|whitening)\b", text_lower):
                extracted["service"] = "Whitening Facial"
            elif re.search(r"\b(d\s*tan\s*facial|detan\s*facial)\b", text_lower):
                extracted["service"] = "D Tan Facial"
            elif re.search(r"\b(d\s*tan\s*cleaner|detan\s*cleaner)\b", text_lower):
                extracted["service"] = "D Tan Cleaner"
            elif re.search(r"\b(face\s*bleach|bleach)\b", text_lower):
                extracted["service"] = "Face Bleach"
            elif re.search(r"\b(keratin|keratin\s*spa)\b", text_lower):
                extracted["service"] = "Keratin Hair Spa"
            elif re.search(r"\b(matrix|loreal|loreal\s*matrix)\b", text_lower):
                extracted["service"] = "Loreal Matrix Hair Spa"
            elif re.search(r"\b(olive|almond)\b", text_lower):
                extracted["service"] = "Head Massage Olive/Almond Oil"
            elif re.search(r"\b(head\s*massage|massage)\b", text_lower):
                extracted["service"] = "Head Massage"
            elif re.search(r"\b(head\s*shave)\b", text_lower):
                extracted["service"] = "Head Shave"
            elif re.search(r"\b(head\s*wash|wash)\b", text_lower):
                extracted["service"] = "Head Wash"
            elif re.search(r"\b(beard|darhi|trim|gaming\s*shave|shave)\b", text_lower):
                extracted["service"] = "Beard Trim / Gaming Shave"
            elif re.search(r"\b(colour|color|dye)\b", text_lower):
                extracted["service"] = "Hair Colour"
            elif re.search(r"\b(haircut|hair\s*cut|cut|baal)\b", text_lower):
                extracted["service"] = "Hair Cut"

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
        time_match = re.search(r"\b([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)?\b", text_lower)
        if time_match:
            hour_str = time_match.group(1)
            min_str = time_match.group(2) or "00"
            meridiem = time_match.group(3)

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
        Classifies intent using regex pattern matches.
        Returns: (intent_name, confidence_score, matched_patterns)
        """
        text_lower = text.lower()
        matched_rules = []
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
                s = [x for x in get_all_services() if x["name"].lower() == service_kw.lower()]
                if s:
                    s_obj = s[0]
                    response_text = f"💰 **{s_obj['name']}** is priced at **₹{int(s_obj['price_inr'])}** (Duration: {s_obj['duration_minutes']} mins). Would you like to book a slot for this?"
                else:
                    response_text = "At Razors-n-scissors, Hair Cut is ₹100, Beard Trim is ₹50, and Head Wash is ₹50. Say 'services' to see the full list."
            else:
                response_text = (
                    "💈 **Razors-n-scissors Price List (FOR BOY'S SALOON):**\n"
                    "• Hair Cut: ₹100\n"
                    "• Head Wash: ₹50\n"
                    "• Head Shave: ₹120\n"
                    "• Beard Trim / Gaming Shave: ₹50\n"
                    "• Head Massage: ₹100\n"
                    "• Head Massage Olive/Almond Oil: ₹150\n"
                    "• Face Bleach: ₹180\n"
                    "• D Tan Cleaner: ₹300\n"
                    "• D Tan Facial: ₹450\n"
                    "• Gold/Diamond Facial with Oxy Bleach: ₹700\n"
                    "• Whitening Facial: ₹600\n"
                    "• Keratin Hair Spa: ₹400\n"
                    "• Loreal Matrix Hair Spa: ₹500\n"
                    "• Hair Colour: ₹450\n"
                    "• Hair Colour & Hair Cut: ₹500\n"
                    "• Anti Dandruff Treatment (3 seatings): ₹1500"
                )

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

        elif intent == "greeting":
            response_text = f"Hello! Welcome to {SALON_NAME} at BH-5. I can help you check prices, services, or book an appointment in seconds. How may I assist you today?"

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
                "(Options: Hair Cut [₹100], Beard Trim [₹50], Head Wash [₹50], "
                "D Tan Facial [₹450], Keratin Hair Spa [₹400], Hair Colour & Cut [₹500], etc.)"
            )

        # Slot 2: Date
        if not self.slots["date"]:
            self.state = "AWAITING_DATE"
            return f"Great choice ({self.slots['service']})! What date would you like to visit? (Say 'today', 'tomorrow', or a date like 2026-11-15)"

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
