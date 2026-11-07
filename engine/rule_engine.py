"""
Approach 1: Classical Rule-Based AI Engine & Finite State Machine (FSM).
Implements:
1. Regex & Keyword Pattern Matchers for Intent Classification
2. Slot-Filling Dialogue State Tracker (Service, Barber, Date, Time, Phone, Name)
3. Step-by-Step Rule Firing & Explainability Trace (Unit II)
"""

import re
from datetime import datetime, timedelta
from database.db import (
    get_all_services, get_all_barbers, get_available_slots,
    book_appointment, cancel_appointment_by_phone, get_appointments_by_phone,
    log_complaint, add_to_handover_queue
)

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
        r"\b(service|services|menu|offer|haircut|fade|beard|shave|facial|spa|color|treatment)\b"
    ],
    "barber_inquiry": [
        r"\b(barber|barbers|stylist|stylists|specialist|vikram|rahul|amit|who\s*works|experience)\b"
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
        r"\b(hygiene|clean|cleanliness|sanitize|sterilize|blade|razor|disposable)\b"
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
    def __init__(self):
        self.state = "IDLE"
        self.slots = {
            "service": None,
            "barber": None,
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
            "barber": None,
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

        # 2. Service Extraction
        services = get_all_services()
        for s in services:
            s_name_lower = s["name"].lower()
            if s_name_lower in text_lower or (s["category"].lower() in text_lower and len(s["category"]) > 3):
                extracted["service"] = s["name"]
                break
        if "service" not in extracted:
            if re.search(r"\b(haircut|hair\s*cut|cut|baal)\b", text_lower):
                extracted["service"] = "Classic Gentleman Haircut"
            elif re.search(r"\b(fade|skin\s*fade|taper)\b", text_lower):
                extracted["service"] = "Skin Fade / Taper Fade"
            elif re.search(r"\b(beard|darhi|trim|shaping)\b", text_lower):
                extracted["service"] = "Royal Beard Trim & Sculpt"
            elif re.search(r"\b(shave|wet\s*shave)\b", text_lower):
                extracted["service"] = "Traditional Hot Towel Wet Shave"
            elif re.search(r"\b(combo|both)\b", text_lower):
                extracted["service"] = "Signature Haircut + Beard Combo"
            elif re.search(r"\b(facial|clean\s*up|detan)\b", text_lower):
                extracted["service"] = "Detan & Charcoal Face Clean-Up"
            elif re.search(r"\b(spa|dandruff)\b", text_lower):
                extracted["service"] = "Revitalizing Anti-Dandruff Hair Spa"
            elif re.search(r"\b(color|grey|coloring)\b", text_lower):
                extracted["service"] = "Beard & Hair Color / Grey Blending"

        # 3. Barber Extraction
        barbers = get_all_barbers()
        for b in barbers:
            first_name = b["name"].split()[0].lower()
            if first_name in text_lower or b["name"].lower() in text_lower:
                extracted["barber"] = b["name"]
                break

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

            # Avoid mistaking 10-digit phone start as time
            if not phone_match or time_match.start() < phone_match.start() or time_match.end() > phone_match.end():
                try:
                    hour = int(hour_str)
                    minute = int(min_str)
                    if meridiem:
                        if meridiem == "pm" and hour < 12:
                            hour += 12
                        elif meridiem == "am" and hour == 12:
                            hour = 0
                    if 8 <= hour <= 21:  # Salon operating range
                        extracted["time_slot"] = f"{hour:02d}:{minute:02d}"
                except ValueError:
                    pass

        # 6. Customer Name Extraction
        name_match = re.search(r"(?:for|name\s*is|i\s*am|this\s*is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        if name_match:
            candidate = name_match.group(1)
            # Ensure not a barber name or service name
            if "Vikram" not in candidate and "Rahul" not in candidate and "Amit" not in candidate:
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
            if v and not self.slots[k]:
                self.slots[k] = v
                trace["rules_fired"].append(f"EXTRACTED_SLOT: {k} = '{v}'")

        # 3. FSM Execution
        response_text = ""

        # Check for immediate escalation
        if intent == "human_handover":
            self.reset_state()
            phone = self.slots.get("phone") or "Customer"
            add_to_handover_queue(phone, user_message, reason="User requested human staff")
            trace["sql_queries"].append("INSERT INTO handover_queue")
            response_text = "🤝 I have notified Mr. Rajesh Kumar (Salon Manager). A staff member will attend to your request right away or call you. You can also reach our desk directly at +91 98765 43210."
            self.state = "IDLE"

        # Check for complaints
        elif intent == "lodge_complaint":
            self.reset_state()
            name = self.slots.get("customer_name") or "Valued Customer"
            phone = self.slots.get("phone") or "Pending"
            cid = log_complaint(name, phone, user_message, severity="HIGH")
            trace["sql_queries"].append(f"INSERT INTO complaints (ID={cid})")
            response_text = f"🙏 We sincerely apologize for your experience. Your complaint has been registered as Ticket #{cid}. Our salon owner personally reviews all tickets and will address this immediately."
            self.state = "IDLE"

        # Check for cancellation
        elif intent == "cancel_appointment":
            phone = self.slots.get("phone")
            if not phone:
                response_text = "To cancel your appointment, please provide your 10-digit registered phone number (e.g., 'Cancel booking for 9876543210')."
                self.state = "AWAITING_CANCEL_PHONE"
            else:
                success, msg = cancel_appointment_by_phone(phone)
                trace["sql_queries"].append(f"UPDATE appointments SET status='CANCELLED' WHERE phone='{phone}'")
                response_text = msg
                self.reset_state()

        # Handle cancellation phone slot state
        elif self.state == "AWAITING_CANCEL_PHONE":
            phone = self.slots.get("phone")
            if phone:
                success, msg = cancel_appointment_by_phone(phone)
                trace["sql_queries"].append(f"UPDATE appointments SET status='CANCELLED' WHERE phone='{phone}'")
                response_text = msg
                self.reset_state()
            else:
                response_text = "Please enter a valid 10-digit mobile number to locate and cancel your reservation."

        # Check status of booking
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
                    response_text = f"📋 Booking Found: #{b['id']} for {b['service_name']} with {b['barber_name']} on {b['appointment_date']} at {b['start_time']}. Status: **{b['status']}**."
                else:
                    response_text = f"No active appointments found for phone ending in {phone[-4:]}."
                self.reset_state()

        # Service / Pricing / FAQ Queries
        elif intent == "pricing_inquiry":
            service_kw = self.slots.get("service")
            if service_kw:
                s = [x for x in get_all_services() if x["name"] == service_kw]
                if s:
                    s_obj = s[0]
                    response_text = f"💰 **{s_obj['name']}** is priced at **₹{int(s_obj['price_inr'])}** (Duration: {s_obj['duration_minutes']} mins). Would you like to book an appointment for this?"
                else:
                    response_text = "Our haircut rates start from ₹250 (Classic) and ₹350 (Fade). Beard styling is ₹200, and our Signature Hair+Beard Combo is ₹450."
            else:
                response_text = "Here is our standard price menu:\n• Classic Haircut: ₹250\n• Skin Fade / Taper: ₹350\n• Beard Sculpting: ₹200\n• Hot Towel Wet Shave: ₹180\n• Signature Hair + Beard Combo: ₹450\n• Charcoal Facial Clean-Up: ₹500\n• Anti-Dandruff Hair Spa: ₹650"

        elif intent == "timing_inquiry":
            response_text = "⏰ **Urban Trim & Groom Salon Hours:**\n• Monday to Friday: 9:00 AM – 9:00 PM\n• Saturday & Sunday: 8:30 AM – 9:30 PM\nWould you like to reserve a time slot today?"

        elif intent == "barber_inquiry":
            barbers = get_all_barbers()
            lines = ["✂️ **Meet Our Master Stylists:**"]
            for b in barbers:
                specs = ", ".join(b["specialties"])
                lines.append(f"• **{b['name']}** ({b['title']}, {b['experience_years']} yrs exp, ⭐ {b['rating']}) — Specializes in {specs}.")
            lines.append("\nYou can book any stylist directly through me!")
            response_text = "\n".join(lines)

        elif intent == "service_inquiry":
            services = get_all_services()
            lines = ["💈 **Urban Trim & Groom Service Menu:**"]
            for s in services:
                lines.append(f"• **{s['name']}** — ₹{int(s['price_inr'])} ({s['duration_minutes']} mins)")
            lines.append("\nWhich service would you like to schedule?")
            response_text = "\n".join(lines)

        elif intent == "payment_inquiry":
            response_text = "💳 We accept all major payment modes: Cash, UPI (Google Pay, PhonePe, Paytm, BHIM), and Debit/Credit Cards. No extra transaction fees."

        elif intent == "parking_inquiry":
            response_text = "🅿️ Yes! Ample free parking for bikes and cars is available right in front of Shop 14, Main Market, Model Town."

        elif intent == "hygiene_inquiry":
            response_text = "🧼 100% Hygiene Guaranteed: We use fresh single-use razor blades for every client, UV autoclave sterilized scissors, and fresh disposable neck wraps."

        elif intent == "walkin_policy":
            response_text = "🚶 Walk-ins are always welcome! However, appointments booked here are prioritized so you don't have to wait during rush hours."

        elif intent == "greeting":
            response_text = "Hello! Welcome to Urban Trim & Groom Barber Salon. I can help you check prices, view master barbers, or book an appointment in seconds. How may I help you today?"

        elif intent == "farewell":
            response_text = "Thank you for connecting with Urban Trim & Groom! Have a great day and see you at the salon. ✂️"

        # Booking Flow Handling (Slot Filling State Machine)
        elif intent == "book_appointment" or self.state.startswith("AWAITING_"):
            response_text = self._handle_slot_filling(trace)

        else:
            # Fallback
            response_text = "I'm not completely sure I understood that. You can ask me about haircut prices, our barber timings, or say 'Book appointment' to reserve a slot."
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
        """Executes slot-filling dialog progression."""
        # Check missing slots in priority order:
        # 1. Service -> 2. Barber -> 3. Date -> 4. Time -> 5. Name -> 6. Phone

        if not self.slots["service"]:
            self.state = "AWAITING_SERVICE"
            return "Sure! Which service would you like? (Options: Classic Haircut, Skin Fade, Beard Sculpt, Hair+Beard Combo, Facial, Hair Spa)"

        if not self.slots["barber"]:
            self.state = "AWAITING_BARBER"
            return f"Great choice ({self.slots['service']})! Which barber would you prefer? You can choose **Vikram Singh**, **Rahul Sharma**, or **Amit Verma** (or say 'Any')."

        if self.slots["barber"] in ["any", "Any", "anyone"]:
            self.slots["barber"] = "Vikram Singh"  # Default master barber

        if not self.slots["date"]:
            self.state = "AWAITING_DATE"
            return "What date would you like to visit? (Say 'today', 'tomorrow', or a date like 2026-11-12)"

        if not self.slots["time_slot"]:
            self.state = "AWAITING_TIME"
            # Show available slots for that barber and date
            slots = get_available_slots(self.slots["barber"], self.slots["date"])[:6]
            slot_str = ", ".join(slots)
            return f"Available times for {self.slots['barber']} on {self.slots['date']}: {slot_str}. What time suits you?"

        if not self.slots["customer_name"]:
            self.state = "AWAITING_NAME"
            return "May I have your name for the reservation?"

        if not self.slots["phone"]:
            self.state = "AWAITING_PHONE"
            return f"Thanks {self.slots['customer_name']}! Please provide your 10-digit mobile number so we can send your confirmation SMS."

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
            return f"🎉 **Booking Confirmed!**\n\n• **Appointment ID:** #{app_id}\n• **Client:** {c_name}\n• **Service:** {s_name}\n• **Barber:** {b_name}\n• **When:** {dt} at {tm}\n• **Contact:** {ph}\n\nWe look forward to styling you at Urban Trim & Groom!"
        else:
            return f"⚠️ {msg}\nWould you like to try another time slot?"
