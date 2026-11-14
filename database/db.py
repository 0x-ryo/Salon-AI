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

    # 7. Salon Holiday / Closed Days Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salon_holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_str TEXT UNIQUE NOT NULL,
        reason TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. Barber Attendance & Daily Roster Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS barber_roster (
        date_str TEXT NOT NULL,
        barber_id TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        PRIMARY KEY (date_str, barber_id)
    )
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

    # Seed or upgrade standard 2-station roster for Razors-n-scissors
    barbers_to_seed = [
        {
            "id": "B1",
            "name": "Station 1",
            "title": "Station 1 Stylist",
            "experience_years": 5,
            "specialties": ["Hair Cut", "Beard Trim", "Hair Colour", "Keratin Spa", "Head Massage"],
            "rating": 4.9,
            "working_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        },
        {
            "id": "B2",
            "name": "Station 2",
            "title": "Station 2 Stylist",
            "experience_years": 5,
            "specialties": ["Hair Cut", "Gaming Shave", "D-Tan Facial", "Head Massage", "Hair Colour"],
            "rating": 4.8,
            "working_days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        }
    ]
    for b in barbers_to_seed:
        cursor.execute("SELECT id, name FROM barbers WHERE id = ?", (b["id"],))
        existing_b = cursor.fetchone()
        if not existing_b:
            cursor.execute("""
            INSERT INTO barbers (id, name, title, experience_years, specialties, rating, working_days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (b["id"], b["name"], b["title"], b["experience_years"],
                  json.dumps(b["specialties"]), b["rating"],
                  json.dumps(b["working_days"])))
        else:
            # Upgrade legacy placeholder names if needed
            if "Staff" in existing_b["name"] or "Vikram" in existing_b["name"] or "Rajesh" in existing_b["name"] or existing_b["name"] != b["name"]:
                cursor.execute("UPDATE barbers SET name = ?, title = ? WHERE id = ?", (b["name"], b["title"], b["id"]))

    # Force purge any legacy barber names in DB
    cursor.execute("UPDATE barbers SET name = 'Station 1', title = 'Station 1 Stylist' WHERE id = 'B1' OR name LIKE '%Vikram%'")
    cursor.execute("UPDATE barbers SET name = 'Station 2', title = 'Station 2 Stylist' WHERE id = 'B2' OR name LIKE '%Rajesh%'")
    cursor.execute("UPDATE appointments SET barber_name = 'Station 1' WHERE barber_id = 'B1' OR barber_name LIKE '%Vikram%' OR barber_name LIKE '%Chair 1%' OR barber_name = 'Razors-n-scissors Staff'")
    cursor.execute("UPDATE appointments SET barber_name = 'Station 2' WHERE barber_id = 'B2' OR barber_name LIKE '%Rajesh%' OR barber_name LIKE '%Chair 2%'")

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
    """Fetch all active station stylists."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM barbers")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        b = dict(r)
        if "2" in str(b.get("id", "")) or "2" in str(b.get("name", "")):
            b["name"] = "Station 2"
            b["title"] = "Station 2 Stylist"
        else:
            b["name"] = "Station 1"
            b["title"] = "Station 1 Stylist"
        b["specialties"] = json.loads(b["specialties"])
        b["working_days"] = json.loads(b["working_days"])
        result.append(b)
    return result


def get_barber_by_name_or_id(identifier=None):
    """Find a barber by ID or partial name, or return default active salon staff."""
    conn = get_connection()
    cursor = conn.cursor()
    id_str = str(identifier).strip().lower() if identifier else ""
    if not identifier or id_str in ["default", "any", "none", "auto"]:
        cursor.execute("SELECT * FROM barbers ORDER BY id ASC LIMIT 1")
    elif "staff" in id_str or "razor" in id_str or id_str in ["b1", "station 1", "station1", "chair 1", "chair1"]:
        cursor.execute("SELECT * FROM barbers WHERE id = 'B1' LIMIT 1")
    elif id_str in ["b2", "station 2", "station2", "chair 2", "chair2"]:
        cursor.execute("SELECT * FROM barbers WHERE id = 'B2' LIMIT 1")
    else:
        cursor.execute("""
        SELECT * FROM barbers 
        WHERE id = ? OR LOWER(name) LIKE ?
        LIMIT 1
        """, (identifier, f"%{id_str}%"))
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT * FROM barbers ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
    conn.close()
    if row:
        b = dict(row)
        b["specialties"] = json.loads(b["specialties"])
        b["working_days"] = json.loads(b["working_days"])
        return b
    return None


def is_salon_closed(date_str: str) -> tuple[bool, str]:
    """Checks whether the salon is marked closed / holiday on a given date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT reason FROM salon_holidays WHERE date_str = ?", (date_str,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return True, row["reason"]
    return False, ""


def set_salon_closed(date_str: str, reason: str = "Salon Holiday / Closed by Owner") -> bool:
    """Marks a specific date as closed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO salon_holidays (date_str, reason)
    VALUES (?, ?)
    ON CONFLICT(date_str) DO UPDATE SET reason = excluded.reason
    """, (date_str, reason))
    conn.commit()
    conn.close()
    return True


def set_salon_open(date_str: str) -> bool:
    """Re-opens the salon for a previously closed date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM salon_holidays WHERE date_str = ?", (date_str,))
    conn.commit()
    conn.close()
    return True


def get_all_holidays() -> list[dict]:
    """Fetches all scheduled closed dates."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM salon_holidays ORDER BY date_str ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_barbers(date_str: str = None) -> list[dict]:
    """
    Returns the list of active barbers on duty for date_str.
    If no explicit roster is set for that date, all barbers in the DB are assumed on duty.
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    all_barbers = get_all_barbers()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT barber_id, is_active FROM barber_roster WHERE date_str = ?", (date_str,))
    roster_rows = {r["barber_id"]: r["is_active"] for r in cursor.fetchall()}
    conn.close()

    active = []
    for b in all_barbers:
        # Default to active (1) if not explicitly recorded as 0
        is_active = roster_rows.get(b["id"], 1)
        if is_active == 1:
            active.append(b)
    return active


def set_barber_attendance(date_str: str, barber_id: str, is_active: bool) -> bool:
    """Sets whether a barber is on duty (1) or on leave (0) on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()
    val = 1 if is_active else 0
    cursor.execute("""
    INSERT INTO barber_roster (date_str, barber_id, is_active)
    VALUES (?, ?, ?)
    ON CONFLICT(date_str, barber_id) DO UPDATE SET is_active = excluded.is_active
    """, (date_str, barber_id, val))
    conn.commit()
    conn.close()
    return True


def get_barber_roster(date_str: str = None) -> list[dict]:
    """Returns all barbers with their on-duty status (True/False) for date_str."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    all_barbers = get_all_barbers()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT barber_id, is_active FROM barber_roster WHERE date_str = ?", (date_str,))
    roster_rows = {r["barber_id"]: r["is_active"] for r in cursor.fetchall()}
    conn.close()

    result = []
    for b in all_barbers:
        b_copy = dict(b)
        b_copy["is_active"] = roster_rows.get(b["id"], 1) == 1
        result.append(b_copy)
    return result


def get_available_slots(barber_id=None, date_str=None):
    """
    Computes available 30-minute time slots between 09:00 and 20:30 on a given date.
    - If salon is closed on date_str -> returns []
    - Dynamically scales capacity based on active barbers on duty:
      - 2 Barbers active -> slot allows 2 concurrent bookings (Chair 1 & Chair 2)
      - 1 Barber active  -> slot allows 1 booking
      - 0 Barbers active -> returns []
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Holiday Check
    closed, _ = is_salon_closed(date_str)
    if closed:
        return []

    # 2. Check active barbers on duty
    active_barbers = get_active_barbers(date_str)
    if not active_barbers:
        return []

    # If a specific barber was requested
    specific_barber = None
    if barber_id and str(barber_id).lower() not in ["default", "any", "none", "auto"]:
        specific_barber = get_barber_by_name_or_id(barber_id)
        if specific_barber:
            # Check if this specific barber is active on duty
            if not any(ab["id"] == specific_barber["id"] for ab in active_barbers):
                return []

    conn = get_connection()
    cursor = conn.cursor()

    # Get all active bookings for this date
    cursor.execute("""
    SELECT barber_id, start_time, end_time FROM appointments
    WHERE appointment_date = ? AND status IN ('BOOKED', 'IN_SERVICE')
    """, (date_str,))
    booked_rows = cursor.fetchall()
    conn.close()

    candidate_slots = [
        "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "12:00", "12:30", "13:00", "14:00", "14:30", "15:00",
        "15:30", "16:00", "16:30", "17:00", "17:30", "18:00",
        "18:30", "19:00", "19:30", "20:00"
    ]

    available = []
    for cand in candidate_slots:
        try:
            cand_dt = datetime.strptime(cand, "%H:%M")
        except Exception:
            continue

        if specific_barber:
            # Check if this specific barber is busy at candidate slot
            busy = False
            for b in booked_rows:
                if b["barber_id"] == specific_barber["id"]:
                    try:
                        b_start = datetime.strptime(b["start_time"], "%H:%M")
                        b_end = datetime.strptime(b["end_time"], "%H:%M")
                        if b_start <= cand_dt < b_end:
                            busy = True
                            break
                    except Exception:
                        if b["start_time"] == cand:
                            busy = True
                            break
            if not busy:
                available.append(cand)
        else:
            # Capacity check: how many active barbers are busy at this slot?
            busy_barber_ids = set()
            for b in booked_rows:
                try:
                    b_start = datetime.strptime(b["start_time"], "%H:%M")
                    b_end = datetime.strptime(b["end_time"], "%H:%M")
                    if b_start <= cand_dt < b_end:
                        busy_barber_ids.add(b["barber_id"])
                except Exception:
                    if b["start_time"] == cand:
                        busy_barber_ids.add(b["barber_id"])

            # Slot is available if at least one active barber is free!
            free_barbers = [ab for ab in active_barbers if ab["id"] not in busy_barber_ids]
            if free_barbers:
                available.append(cand)

    return available


def book_appointment(customer_name, phone, service_id, barber_id=None, date_str=None, time_str=None):
    """
    Creates a new appointment with strict interval conflict detection and dynamic chair allocation.
    Supports single or multi-service combinations (e.g. 'Hair Cut + Beard Trim').
    Returns (success: bool, message: str, appointment_id: int or None)
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Holiday Check
    closed, reason = is_salon_closed(date_str)
    if closed:
        return False, f"Razors-n-scissors is closed on {date_str} ({reason}). No appointments can be booked on this day.", None

    # 2. Service resolution
    service = get_service_by_name_or_id(service_id)
    if not service:
        return False, f"Service '{service_id}' could not be found.", None

    # 3. Calculate end time
    try:
        start_dt = datetime.strptime(time_str, "%H:%M")
        end_dt = start_dt + timedelta(minutes=service["duration_minutes"])
        end_time_str = end_dt.strftime("%H:%M")
    except ValueError:
        return False, "Invalid time format. Please provide HH:MM in 24-hr format.", None

    # 4. Active Barbers & Chair Allocation
    active_barbers = get_active_barbers(date_str)
    if not active_barbers:
        return False, f"No styling staff are on duty on {date_str}. The salon is inactive on this day.", None

    conn = get_connection()
    cursor = conn.cursor()

    # Determine candidate barbers
    assigned_barber = None
    if barber_id and str(barber_id).lower() not in ["default", "any", "none", "auto"]:
        target_b = get_barber_by_name_or_id(barber_id)
        if not target_b or not any(ab["id"] == target_b["id"] for ab in active_barbers):
            b_name = target_b["name"] if target_b else barber_id
            conn.close()
            return False, f"Stylist '{b_name}' is not on duty on {date_str}.", None

        # Check conflict for this specific barber
        cursor.execute("""
        SELECT id, customer_name, start_time, end_time FROM appointments
        WHERE barber_id = ? 
          AND appointment_date = ? 
          AND status IN ('BOOKED', 'IN_SERVICE')
          AND start_time < ? 
          AND end_time > ?
        """, (target_b["id"], date_str, end_time_str, time_str))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return False, f"Sorry, {target_b['name']} is already booked / busy from {existing['start_time']} to {existing['end_time']} on {date_str}. Please choose another time slot.", None
        assigned_barber = target_b
    else:
        # Auto-assign to first available active barber on duty
        for ab in active_barbers:
            cursor.execute("""
            SELECT id, customer_name, start_time, end_time FROM appointments
            WHERE barber_id = ? 
              AND appointment_date = ? 
              AND status IN ('BOOKED', 'IN_SERVICE')
              AND start_time < ? 
              AND end_time > ?
            """, (ab["id"], date_str, end_time_str, time_str))
            existing = cursor.fetchone()
            if not existing:
                assigned_barber = ab
                break

        if not assigned_barber:
            conn.close()
            cap_str = f"All {len(active_barbers)} chairs" if len(active_barbers) > 1 else "The chair"
            return False, f"Sorry, {cap_str} on duty are fully booked from {time_str} to {end_time_str} on {date_str}. Please choose another time slot.", None

    cursor.execute("""
    INSERT INTO appointments (customer_name, phone, service_id, service_name, barber_id, barber_name, appointment_date, start_time, end_time, price_inr, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'BOOKED')
    """, (customer_name, phone, service["id"], service["name"], assigned_barber["id"], assigned_barber["name"], date_str, time_str, end_time_str, service["price_inr"]))

    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return True, f"Appointment #{appointment_id} confirmed for {customer_name} with {assigned_barber['name']} on {date_str} at {time_str} ({service['name']} - ₹{int(service['price_inr'])}).", appointment_id


def book_walkin_appointment(customer_name: str, phone: str, service_id: str, barber_id: str = None, time_str: str = None) -> tuple[bool, str, int | None]:
    """Immediate counter walk-in reservation with automatic station assignment."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not time_str:
        time_str = datetime.now().strftime("%H:%M")
    return book_appointment(customer_name, phone, service_id, barber_id=barber_id, date_str=today_str, time_str=time_str)


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
    apps = []
    for r in rows:
        app = dict(r)
        if "2" in str(app.get("barber_id", "")) or "2" in str(app.get("barber_name", "")):
            app["barber_name"] = "Station 2"
        else:
            app["barber_name"] = "Station 1"
        apps.append(app)
    return apps


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
    today_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Active Bookings & Revenue (Overall)
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price_inr), 0) FROM appointments WHERE status = 'BOOKED'")
    booked_row = cursor.fetchone()
    active_count = booked_row[0] if booked_row else 0
    active_revenue = booked_row[1] if booked_row else 0.0

    # Total Completed (Overall)
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price_inr), 0) FROM appointments WHERE status = 'COMPLETED'")
    comp_row = cursor.fetchone()
    completed_count = comp_row[0] if comp_row else 0
    completed_revenue = comp_row[1] if comp_row else 0.0

    # Today's Specific Operations
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = ?", (today_str,))
    today_total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = 'IN_SERVICE'", (today_str,))
    today_in_service = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price_inr), 0) FROM appointments WHERE appointment_date = ? AND status = 'COMPLETED'", (today_str,))
    t_comp_row = cursor.fetchone()
    today_completed = t_comp_row[0] if t_comp_row else 0
    today_completed_rev = t_comp_row[1] if t_comp_row else 0.0

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(price_inr), 0) FROM appointments WHERE appointment_date = ? AND status = 'BOOKED'", (today_str,))
    t_booked_row = cursor.fetchone()
    today_booked = t_booked_row[0] if t_booked_row else 0
    today_booked_rev = t_booked_row[1] if t_booked_row else 0.0

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

    # Salon status & active barbers
    closed_today, closed_reason = is_salon_closed(today_str)
    active_barbers = get_active_barbers(today_str)
    all_barbers = get_all_barbers()

    return {
        "active_bookings": active_count,
        "active_revenue_inr": active_revenue,
        "completed_bookings": completed_count,
        "completed_revenue_inr": completed_revenue,
        "total_revenue_inr": active_revenue + completed_revenue,
        "today_total_bookings": today_total,
        "today_in_service": today_in_service,
        "today_completed": today_completed,
        "today_completed_revenue_inr": today_completed_rev,
        "today_booked_revenue_inr": today_booked_rev,
        "is_today_closed": closed_today,
        "today_closed_reason": closed_reason,
        "active_barbers_count": len(active_barbers),
        "total_barbers_count": len(all_barbers),
        "pending_handovers": pending_handovers,
        "open_complaints": open_complaints,
        "top_services": top_services
    }
