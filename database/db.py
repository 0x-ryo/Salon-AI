"""
Database Management Module for Urban Trim & Groom Barber Salon.
Handles SQLite relational storage for services, barbers, appointments,
complaints, human handovers, and conversation audit logs.
"""

import sqlite3
import json
import os
import re
from datetime import datetime, timedelta

DB_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DB_DIR)
DB_PATH = os.path.join(DB_DIR, "salon.db")
KB_PATH = os.path.join(PROJECT_ROOT, "data", "knowledge_base.json")


def get_connection():
    """Returns a SQLite database connection with row factory enabled and WAL mode."""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
    except Exception:
        pass
    return conn


def init_db():
    """Initializes tables and seeds initial data from knowledge_base.json."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Services Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        duration_minutes INTEGER NOT NULL,
        price_inr REAL NOT NULL
    )
    """)

    # 2. Barbers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS barbers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        title TEXT NOT NULL,
        experience_years INTEGER NOT NULL,
        specialties TEXT NOT NULL,
        rating REAL NOT NULL,
        working_days TEXT NOT NULL
    )
    """)

    # 3. Appointments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        service_id TEXT NOT NULL,
        service_name TEXT NOT NULL,
        barber_id TEXT NOT NULL,
        barber_name TEXT NOT NULL,
        appointment_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        price_inr REAL NOT NULL,
        status TEXT DEFAULT 'BOOKED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id),
        FOREIGN KEY (barber_id) REFERENCES barbers (id)
    )
    """)

    # 4. Complaints Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT NOT NULL,
        complaint_text TEXT NOT NULL,
        severity TEXT DEFAULT 'MEDIUM',
        status TEXT DEFAULT 'OPEN',
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 5. Human Handover Queue Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS handover_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_phone TEXT,
        last_query TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Audit & Analytics Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        user_message TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        detected_intent TEXT,
        confidence REAL,
        engine_used TEXT,
        latency_ms REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Salon Settings Table (Store Closure, Capacity, Active Barbers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salon_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    default_settings = {
        "active_barbers": "2",
        "is_closed": "0",
        "closure_reason": "",
        "closed_dates": "[]"
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO salon_settings (key, value) VALUES (?, ?)", (k, v))

    # Ensure Chair 1 and Chair 2 exist
    cursor.execute("""
    INSERT OR IGNORE INTO barbers (id, name, title, experience_years, specialties, rating, working_days)
    VALUES ('B1', 'Razors-n-scissors Staff', 'Senior Stylist (Chair 1)', 5, '["Hair Cut", "Beard Trim", "Hair Spa"]', 4.9, '["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]')
    """)
    cursor.execute("""
    INSERT OR IGNORE INTO barbers (id, name, title, experience_years, specialties, rating, working_days)
    VALUES ('B2', 'Stylist 2 (Chair 2)', 'Grooming Specialist (Chair 2)', 4, '["Hair Cut", "Facials", "Styling"]', 4.8, '["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]')
    """)

    conn.commit()

    # Seed data from knowledge_base.json if services table is empty
    cursor.execute("SELECT COUNT(*) as count FROM services")
    if cursor.fetchone()["count"] == 0 and os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)

        for s in kb.get("services", []):
            cursor.execute("""
            INSERT INTO services (id, category, name, description, duration_minutes, price_inr)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (s["id"], s["category"], s["name"], s.get("description", ""), s["duration_minutes"], s["price_inr"]))

        # Always seed a default barber entry for Razors-n-scissors
        default_barbers = kb.get("barbers", [
            {
                "id": "B1",
                "name": "Razors-n-scissors Staff",
                "title": "Professional Barber",
                "experience_years": 5,
                "specialties": ["Hair Cut", "Beard Trim", "Hair Spa"],
                "rating": 4.8,
                "working_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            }
        ])
        for b in default_barbers:
            cursor.execute("""
            INSERT INTO barbers (id, name, title, experience_years, specialties, rating, working_days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (b["id"], b["name"], b.get("title","Barber"), b.get("experience_years",5),
                  json.dumps(b.get("specialties",[])), b.get("rating",5.0),
                  json.dumps(b.get("working_days",[]))))

        # Seed a sample upcoming appointment
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO appointments (customer_name, phone, service_id, service_name, barber_id, barber_name, appointment_date, start_time, end_time, price_inr, status)
        VALUES ('Demo Customer', '6284421638', 'S1', 'Hair Cut', 'B1', 'Razors-n-scissors Staff', ?, '10:00', '10:20', 100, 'BOOKED')
        """, (today_str,))

        conn.commit()

    conn.close()


def get_all_services():
    """Fetch all services sorted by category and price."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services ORDER BY category, price_inr")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_service_by_name_or_id(identifier):
    """Find a service by ID, fuzzy name match, or multi-service combo joined with '+'."""
    if not identifier:
        return None
    if isinstance(identifier, str) and "+" in identifier:
        parts = [p.strip() for p in identifier.split("+") if p.strip()]
        total_price = 0.0
        total_duration = 0
        names = []
        for p in parts:
            s_obj = get_service_by_name_or_id(p)
            if s_obj:
                total_price += float(s_obj["price_inr"])
                total_duration += int(s_obj["duration_minutes"])
                names.append(s_obj["name"])
        if names:
            # Combo discount: Haircut + Beard combo is ₹140
            if "Hair Cut" in names and any("Beard" in n for n in names) and len(names) == 2:
                total_price = 140.0
            return {
                "id": "+".join(parts),
                "name": " + ".join(names),
                "price_inr": total_price,
                "duration_minutes": max(total_duration, 20),
                "category": "Combo Package"
            }

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM services 
    WHERE id = ? OR LOWER(name) LIKE ?
    LIMIT 1
    """, (identifier, f"%{str(identifier).lower()}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_barbers():
    """Fetch all active barbers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM barbers")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        b = dict(r)
        b["specialties"] = json.loads(b["specialties"])
        b["working_days"] = json.loads(b["working_days"])
        result.append(b)
    return result


def get_barber_by_name_or_id(identifier=None):
    """Find a barber by ID or partial name, or return default salon staff."""
    conn = get_connection()
    cursor = conn.cursor()
    if not identifier or str(identifier).lower() in ["default", "any", "staff", "b1", "none"]:
        cursor.execute("SELECT * FROM barbers LIMIT 1")
    else:
        cursor.execute("""
        SELECT * FROM barbers 
        WHERE id = ? OR LOWER(name) LIKE ?
        LIMIT 1
        """, (identifier, f"%{str(identifier).lower()}%"))
    row = cursor.fetchone()
    conn.close()
    if row:
        b = dict(row)
        b["specialties"] = json.loads(b["specialties"])
        b["working_days"] = json.loads(b["working_days"])
        return b
    return None


def get_salon_setting(key: str, default: str = "") -> str:
    """Retrieves a salon operational setting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM salon_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_salon_setting(key: str, value: str):
    """Sets a salon operational setting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO salon_settings (key, value) VALUES (?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()


def get_all_salon_settings() -> dict:
    """Returns all settings as a key-value dictionary."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM salon_settings")
    rows = cursor.fetchall()
    conn.close()
    settings = {r["key"]: r["value"] for r in rows}
    settings.setdefault("active_barbers", "2")
    settings.setdefault("is_closed", "0")
    settings.setdefault("closure_reason", "")
    settings.setdefault("closed_dates", "[]")
    return settings


def is_salon_closed_on(date_str: str) -> tuple[bool, str]:
    """Checks if salon is closed on a specific date (either today toggle or scheduled holiday)."""
    settings = get_all_salon_settings()
    is_closed_toggle = settings.get("is_closed", "0") == "1"
    closure_reason = settings.get("closure_reason", "").strip() or "Salon is closed for operations."
    today_str = datetime.now().strftime("%Y-%m-%d")

    if is_closed_toggle and date_str == today_str:
        return True, closure_reason

    try:
        closed_dates = json.loads(settings.get("closed_dates", "[]"))
        if date_str in closed_dates:
            return True, closure_reason or f"Salon is closed on {date_str} (Scheduled Holiday)."
    except Exception:
        pass

    return False, ""


def get_available_slots(barber_id=None, date_str=None):
    """
    Computes available 30-minute time slots between 09:00 and 20:30 on a given date.
    Respects:
    1. Salon Closure: returns [] if date is marked closed/holiday.
    2. Dynamic Capacity: 
       - If active_barbers == 1: max 1 booking allowed per slot across salon.
       - If active_barbers == 2: max 2 bookings allowed per slot across salon (Chair 1 & Chair 2).
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    closed, reason = is_salon_closed_on(date_str)
    if closed:
        return []

    try:
        active_capacity = int(get_salon_setting("active_barbers", "2"))
    except Exception:
        active_capacity = 2

    conn = get_connection()
    cursor = conn.cursor()

    b_id = None
    if barber_id and str(barber_id).lower() not in ["default", "any", "staff", "none", "razors-n-scissors staff"]:
        b = get_barber_by_name_or_id(barber_id)
        if b:
            b_id = b["id"]

    cursor.execute("""
    SELECT barber_id, barber_name, start_time, end_time FROM appointments
    WHERE appointment_date = ? AND status = 'BOOKED'
    """, (date_str,))
    booked_slots = cursor.fetchall()
    conn.close()

    def is_slot_busy(candidate):
        try:
            cand_dt = datetime.strptime(candidate, "%H:%M")
            if b_id:
                for b in booked_slots:
                    if b["barber_id"] == b_id:
                        try:
                            b_start = datetime.strptime(b["start_time"], "%H:%M")
                            b_end = datetime.strptime(b["end_time"], "%H:%M")
                            if b_start <= cand_dt < b_end:
                                return True
                        except Exception:
                            if b["start_time"] == candidate:
                                return True
                return False

            busy_chairs = 0
            for b in booked_slots:
                try:
                    b_start = datetime.strptime(b["start_time"], "%H:%M")
                    b_end = datetime.strptime(b["end_time"], "%H:%M")
                    if b_start <= cand_dt < b_end:
                        busy_chairs += 1
                except Exception:
                    if b["start_time"] == candidate:
                        busy_chairs += 1
            return busy_chairs >= active_capacity
        except Exception:
            return False

    candidate_slots = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "14:00", "14:30", "15:00",
        "15:30", "16:00", "16:30", "17:00", "17:30", "18:00",
        "18:30", "19:00", "19:30", "20:00"
    ]

    available = [slot for slot in candidate_slots if not is_slot_busy(slot)]
    return available


def book_appointment(customer_name, phone, service_id, barber_id=None, date_str=None, time_str=None):
    """
    Creates a new appointment with strict interval conflict detection, store closure check, and dynamic chair capacity.
    Supports single or multi-service combinations (e.g. 'Hair Cut + Beard Trim').
    Returns (success: bool, message: str, appointment_id: int or None)
    """
    if not date_str or not time_str:
        return False, "Date and time must be provided.", None

    # 1. Check Salon Closure
    closed, reason = is_salon_closed_on(date_str)
    if closed:
        return False, f"Sorry, Razors-n-scissors is closed on {date_str} ({reason}). No appointments can be accepted.", None

    service = get_service_by_name_or_id(service_id)
    if not service:
        return False, f"Service '{service_id}' could not be found.", None

    try:
        start_dt = datetime.strptime(time_str, "%H:%M")
        end_dt = start_dt + timedelta(minutes=service["duration_minutes"])
        end_time_str = end_dt.strftime("%H:%M")
    except ValueError:
        return False, "Invalid time format. Please provide HH:MM in 24-hr format.", None

    try:
        active_capacity = int(get_salon_setting("active_barbers", "2"))
    except Exception:
        active_capacity = 2

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, customer_name, barber_id, barber_name, start_time, end_time FROM appointments
    WHERE appointment_date = ? 
      AND status = 'BOOKED'
      AND start_time < ? 
      AND end_time > ?
    """, (date_str, end_time_str, time_str))
    overlapping = cursor.fetchall()

    specific_barber = None
    if barber_id and str(barber_id).lower() not in ["default", "any", "staff", "none"]:
        b = get_barber_by_name_or_id(barber_id)
        if b:
            specific_barber = b

    if specific_barber:
        barber_conflict = [o for o in overlapping if o["barber_id"] == specific_barber["id"] or o["barber_name"] == specific_barber["name"]]
        if barber_conflict:
            conn.close()
            c = barber_conflict[0]
            return False, f"Sorry, {specific_barber['name']} is already booked / busy from {c['start_time']} to {c['end_time']} on {date_str}. Please choose another time slot.", None
        assigned_id = specific_barber["id"]
        assigned_name = specific_barber["name"]
    else:
        if len(overlapping) >= active_capacity:
            conn.close()
            chair_word = "styling chair" if active_capacity == 1 else "styling chairs"
            return False, f"Sorry, all {active_capacity} {chair_word} are already fully booked from {time_str} to {end_time_str} on {date_str}. Please choose another time slot.", None

        booked_chairs = [o["barber_id"] for o in overlapping]
        if "B1" not in booked_chairs:
            assigned_id = "B1"
            assigned_name = "Stylist 1 (Chair 1)"
        elif active_capacity >= 2 and "B2" not in booked_chairs:
            assigned_id = "B2"
            assigned_name = "Stylist 2 (Chair 2)"
        else:
            assigned_id = f"B{len(overlapping) + 1}"
            assigned_name = f"Stylist Station {len(overlapping) + 1}"

    cursor.execute("""
    INSERT INTO appointments (customer_name, phone, service_id, service_name, barber_id, barber_name, appointment_date, start_time, end_time, price_inr, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BOOKED')
    """, (customer_name, phone, service["id"], service["name"], assigned_id, assigned_name, date_str, time_str, end_time_str, service["price_inr"]))

    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return True, f"Appointment #{appointment_id} confirmed for {customer_name} ({assigned_name}) on {date_str} at {time_str} ({service['name']} - ₹{int(service['price_inr'])}).", appointment_id


def cancel_appointment_by_phone(phone):
    """Cancels the most recent booked appointment for a phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    clean_digits = re.sub(r"\D", "", str(phone))
    clean_10 = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
    cursor.execute("""
    SELECT id, service_name, appointment_date, start_time, barber_name FROM appointments
    WHERE (phone LIKE ? OR phone = ?) AND status = 'BOOKED'
    ORDER BY appointment_date DESC, start_time DESC
    LIMIT 1
    """, (f"%{clean_10}%", str(phone)))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, f"No active bookings found for phone number ending in {phone[-4:]}."

    cursor.execute("UPDATE appointments SET status = 'CANCELLED' WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return True, f"Appointment #{row['id']} for {row['service_name']} with {row['barber_name']} on {row['appointment_date']} at {row['start_time']} has been successfully cancelled."


def cancel_appointment_by_slot(date_str, time_str, barber_id=None):
    """Cancels any booked appointment at a specific slot (for test isolation)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE appointments SET status = 'CANCELLED'
    WHERE appointment_date = ? AND start_time = ? AND status = 'BOOKED'
    """, (date_str, time_str))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count > 0


def get_appointments_by_phone(phone):
    """Finds all bookings (past & present) for a customer phone number."""
    conn = get_connection()
    cursor = conn.cursor()
    clean_digits = re.sub(r"\D", "", str(phone))
    clean_10 = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
    cursor.execute("""
    SELECT * FROM appointments 
    WHERE phone LIKE ? OR phone = ? 
    ORDER BY appointment_date DESC, start_time DESC
    """, (f"%{clean_10}%", str(phone)))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_appointments(date_filter=None):
    """Fetches appointments for manager dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    if date_filter:
        cursor.execute("SELECT * FROM appointments WHERE appointment_date = ? ORDER BY start_time ASC", (date_filter,))
    else:
        cursor.execute("SELECT * FROM appointments ORDER BY appointment_date DESC, start_time ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_complaint(customer_name, phone, complaint_text, severity="MEDIUM"):
    """Logs customer feedback or grievance into complaints table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO complaints (customer_name, phone, complaint_text, severity, status)
    VALUES (?, ?, ?, ?, 'OPEN')
    """, (customer_name, phone, complaint_text, severity))
    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return complaint_id


def get_all_complaints():
    """Fetches all customer complaints for manager portal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_complaint(complaint_id, notes):
    """Updates complaint resolution status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE complaints SET status = 'RESOLVED', resolution_notes = ? WHERE id = ?
    """, (notes, complaint_id))
    conn.commit()
    conn.close()


def add_to_handover_queue(customer_phone, last_query, reason="Unresolved or complex inquiry"):
    """Adds a customer to the human staff escalation queue."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO handover_queue (customer_phone, last_query, reason, status)
    VALUES (?, ?, ?, 'PENDING')
    """, (customer_phone, last_query, reason))
    handover_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return handover_id


def get_handover_queue():
    """Fetches pending handovers for the staff dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM handover_queue WHERE status = 'PENDING' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_handover(handover_id):
    """Marks a human handover as handled."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE handover_queue SET status = 'RESOLVED' WHERE id = ?", (handover_id,))
    conn.commit()
    conn.close()


def log_chat_interaction(session_id, user_message, bot_response, intent, confidence, engine, latency_ms):
    """Logs conversation interaction for explainability and evaluation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO chat_logs (session_id, user_message, bot_response, detected_intent, confidence, engine_used, latency_ms)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, user_message, bot_response, intent, confidence, engine, latency_ms))
    conn.commit()
    conn.close()


def get_chat_logs(limit=50):
    """Fetches conversation logs for audit and teacher inspection."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_appointment_status(appointment_id: int, new_status: str) -> bool:
    """Updates the status of an appointment (e.g. COMPLETED, CANCELLED, BOOKED)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status.upper(), appointment_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def get_live_metrics() -> dict:
    """Computes real-time KPIs for owner dashboard and API."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Active Bookings & Revenue
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price_inr), 0) FROM appointments WHERE status = 'BOOKED'")
    booked_row = cursor.fetchone()
    active_count = booked_row[0] if booked_row else 0
    active_revenue = booked_row[1] if booked_row else 0.0

    # Total Completed
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price_inr), 0) FROM appointments WHERE status = 'COMPLETED'")
    comp_row = cursor.fetchone()
    completed_count = comp_row[0] if comp_row else 0
    completed_revenue = comp_row[1] if comp_row else 0.0

    # Pending Handovers
    cursor.execute("SELECT COUNT(*) FROM handover_queue WHERE status = 'PENDING'")
    pending_handovers = cursor.fetchone()[0]

    # Open Complaints
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'OPEN'")
    open_complaints = cursor.fetchone()[0]

    # Service Popularity
    cursor.execute("""
    SELECT service_name, COUNT(*) as cnt 
    FROM appointments 
    GROUP BY service_name 
    ORDER BY cnt DESC LIMIT 5
    """)
    top_services = [{"service": r[0], "count": r[1]} for r in cursor.fetchall()]

    conn.close()
    return {
        "active_bookings": active_count,
        "active_revenue_inr": active_revenue,
        "completed_bookings": completed_count,
        "completed_revenue_inr": completed_revenue,
        "total_revenue_inr": active_revenue + completed_revenue,
        "pending_handovers": pending_handovers,
        "open_complaints": open_complaints,
        "top_services": top_services
    }
