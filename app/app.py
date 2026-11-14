"""
Razors-n-scissors Barber Salon — Front Desk Reception Command Portal
Inspired by Pulse Clinic Front-Desk Architecture
INT428 Project 13 · Suman Saha (Reg: 12524973)

Features:
- Live Front Desk Operations & Dual-Chair Station Allocation (Chair 1 & Chair 2)
- One-Click Salon Holiday & Closure Controller (Stops bookings on closed days)
- Multi-Barber Roster Capacity Scaling (1 Barber = 1 slot, 2 Barbers = 2 slots)
- Instant Counter Walk-In Booking & Seating Workflow
- Real-Time Appointment Queue with Seating (In-Service) & Completion Actions
- Financial Revenue Tracking (Total, Cash, UPI)
- Academic AI Lab & Benchmarks isolated into dedicated sidebar page
"""

import os
import sys
import json
import time
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Path resolution
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

for path in [PROJECT_ROOT, APP_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS, TAGLINE
except Exception:
    SALON_NAME = "Razors-n-scissors"
    PHONE_WHATSAPP = "+91 6284421638"
    ADDRESS = "BH-5, Lovely Professional University Campus, Phagwara, Punjab"
    OPERATING_HOURS = "Mon–Sun: 9:00 AM – 9:00 PM"
    TAGLINE = "Groom yourself at Razors-n-scissors"

from database.db import (
    init_db, get_all_services, get_all_barbers, get_all_appointments,
    get_all_complaints, resolve_complaint, get_handover_queue, resolve_handover,
    get_live_metrics, update_appointment_status, is_salon_closed,
    set_salon_closed, set_salon_open, get_all_holidays, get_active_barbers,
    set_barber_attendance, get_barber_roster, book_appointment, book_walkin_appointment
)

# Page Setup
st.set_page_config(
    page_title=f"{SALON_NAME} | Front Desk Portal",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Schema
init_db()

# Remote 24/7 Cloud API URL on Render
LIVE_API_BASE = os.environ.get("SALON_LIVE_API", "https://salon-ai-backend-6xdf.onrender.com")

# ----------------- MODERN PULSE CLINIC UI STYLING -----------------
st.markdown("""
<style>
    /* Global Clean Font and Background */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Pulse Clinic Top Header Card */
    .reception-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 22px;
        color: #F8FAFC;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .reception-title {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #FFFFFF;
    }
    .reception-subtitle {
        color: #94A3B8;
        font-size: 0.92rem;
        margin-top: 4px;
        margin-bottom: 0;
    }

    /* Metric Cards Inspired by Pulse Clinic */
    div[data-testid="stMetric"] {
        background: #111827 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 14px !important;
        padding: 16px 20px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #3B82F6 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
    }

    /* Station Chairs Container */
    .station-card {
        background: #111827;
        border: 1px solid #1F2937;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .station-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #F1F5F9;
        margin-bottom: 4px;
    }
    .station-sub {
        font-size: 0.82rem;
        color: #94A3B8;
    }

    /* Status Pills */
    .badge-booked {
        background: rgba(59, 130, 246, 0.15);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-inservice {
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-completed {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-cancelled {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }

    /* Shop Status Pill */
    .pill-open {
        background: rgba(16, 185, 129, 0.12);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .pill-closed {
        background: rgba(239, 68, 68, 0.12);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .pill-sync {
        background: rgba(59, 130, 246, 0.12);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Queue Row Styling */
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #1F2937 !important;
        background: #0B0F19 !important;
    }
</style>
""", unsafe_allow_html=True)


# ----------------- LIVE CLOUD DATA FETCHER -----------------
def fetch_live_cloud_data():
    """Fetches real-time appointments and metrics with local DB fallback."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        resp_apps = requests.get(f"{LIVE_API_BASE}/api/appointments", timeout=2.2)
        resp_metrics = requests.get(f"{LIVE_API_BASE}/api/metrics", timeout=2.2)
        resp_handovers = requests.get(f"{LIVE_API_BASE}/api/handovers", timeout=2.2)
        resp_complaints = requests.get(f"{LIVE_API_BASE}/api/complaints", timeout=2.2)
        resp_holidays = requests.get(f"{LIVE_API_BASE}/api/holidays", timeout=2.2)
        resp_roster = requests.get(f"{LIVE_API_BASE}/api/roster?date_str={today_str}", timeout=2.2)

        if resp_apps.status_code == 200 and resp_metrics.status_code == 200:
            return {
                "source": "LIVE_CLOUD",
                "appointments": resp_apps.json(),
                "metrics": resp_metrics.json(),
                "handovers": resp_handovers.json() if resp_handovers.status_code == 200 else [],
                "complaints": resp_complaints.json() if resp_complaints.status_code == 200 else [],
                "holidays": resp_holidays.json() if resp_holidays.status_code == 200 else [],
                "roster": resp_roster.json() if resp_roster.status_code == 200 else []
            }
    except Exception:
        pass

    # Local SQLite Fallback
    return {
        "source": "LOCAL_DB",
        "appointments": get_all_appointments(),
        "metrics": get_live_metrics(),
        "handovers": get_handover_queue(),
        "complaints": get_all_complaints(),
        "holidays": get_all_holidays(),
        "roster": get_barber_roster(today_str)
    }


def send_action_update(action_type: str, payload: dict = None):
    """Dispatches action updates to Render backend and applies locally."""
    payload = payload or {}
    try:
        if action_type == "status":
            requests.post(f"{LIVE_API_BASE}/api/action/status", json=payload, timeout=2.0)
        elif action_type == "holiday":
            requests.post(f"{LIVE_API_BASE}/api/action/holiday", json=payload, timeout=2.0)
        elif action_type == "roster":
            requests.post(f"{LIVE_API_BASE}/api/action/roster", json=payload, timeout=2.0)
        elif action_type == "handover":
            requests.post(f"{LIVE_API_BASE}/api/action/handover", json=payload, timeout=2.0)
        elif action_type == "complaint":
            requests.post(f"{LIVE_API_BASE}/api/action/complaint", json=payload, timeout=2.0)
        elif action_type == "walkin":
            requests.post(f"{LIVE_API_BASE}/api/action/book", json=payload, timeout=2.0)
    except Exception:
        pass

    # Apply locally as well for immediate consistency
    if action_type == "status":
        update_appointment_status(payload.get("id", 0), payload.get("status", "COMPLETED"))
    elif action_type == "holiday":
        if payload.get("is_closed"):
            set_salon_closed(payload.get("date_str"), payload.get("reason", "Shop Holiday"))
        else:
            set_salon_open(payload.get("date_str"))
    elif action_type == "roster":
        set_barber_attendance(payload.get("date_str"), payload.get("barber_id"), payload.get("is_active"))
    elif action_type == "handover":
        resolve_handover(payload.get("id"))
    elif action_type == "complaint":
        resolve_complaint(payload.get("id"), payload.get("notes", "Resolved at counter"))
    elif action_type == "walkin":
        book_appointment(
            customer_name=payload.get("customer_name"),
            phone=payload.get("phone"),
            service_id=payload.get("service_id"),
            barber_id=payload.get("barber_id"),
            date_str=payload.get("date_str"),
            time_str=payload.get("time_str")
        )


# ----------------- SESSION STATE -----------------
today_str = datetime.now().strftime("%Y-%m-%d")
if "last_sync" not in st.session_state:
    st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.markdown(f"## 💈 {SALON_NAME}")
    st.caption("Front Desk Operations & Staff Command")

    st.markdown(f"**📍 Location:** {ADDRESS}")
    st.markdown(f"**⏰ Timings:** {OPERATING_HOURS}")
    st.markdown(f"**📱 WhatsApp:** `{PHONE_WHATSAPP}`")
    st.markdown(f"[🔗 **Pair WhatsApp Cloud Bot**]({LIVE_API_BASE}/pair)")

    st.divider()

    st.markdown("### ⚡ Live Counter Sync")
    auto_refresh = st.toggle("Auto-Refresh (30s)", value=False, help="Enable automatic background refresh every 30 seconds. Disabled by default to prevent screen flicker.")
    if st.button("🔄 Refresh Counter Data", use_container_width=True):
        st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")
        st.rerun()

    st.caption(f"Last updated: {st.session_state.last_sync}")

    st.divider()
    st.markdown("### 🔬 Academic AI Evaluation")
    st.markdown("The INT428 comparative benchmark (Approach 1 vs 2 vs Hybrid) runs autonomously in the background.")
    st.page_link("pages/1_🔬_AI_Evaluation_&_Benchmarks.py", label="Open AI Benchmark Lab 🔬", icon="📊")

    st.divider()
    st.caption("INT428: Artificial Intelligence Essentials · Group 13")


# ----------------- LOAD DATA -----------------
live_data = fetch_live_cloud_data()
all_apps = live_data["appointments"]
metrics = live_data["metrics"]
pending_handovers = [h for h in live_data["handovers"] if h.get("status") == "PENDING"]
open_complaints = [c for c in live_data["complaints"] if c.get("status") == "OPEN"]
holidays = live_data.get("holidays", [])
roster = live_data.get("roster", [])

# Determine today's salon status & capacity
is_closed_today, closed_reason = is_salon_closed(today_str)
active_barbers = get_active_barbers(today_str)
active_barber_count = len(active_barbers)

# ----------------- 1. RECEPTION HEADER (PULSE CLINIC HERO) -----------------
st.markdown(f"""
<div class="reception-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
            <h1 class="reception-title">💈 {SALON_NAME} · Front Desk Reception</h1>
            <p class="reception-subtitle">Campus Grooming Hub · {ADDRESS} · {datetime.now().strftime('%A, %B %d, %Y')}</p>
        </div>
        <div style="display:flex; align-items:center; gap:10px;">
            {'<span class="pill-closed">🔴 Salon Closed Today</span>' if is_closed_today else f'<span class="pill-open">🟢 Salon Open · {active_barber_count} Station(s) Active</span>'}
            <span class="pill-sync">● Cloud Sync Active</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- ACADEMIC AI LAB BANNER & DISCOVERY -----------------
with st.container(border=True):
    col_lab_text, col_lab_btn = st.columns([3, 1])
    with col_lab_text:
        st.markdown("🔬 **INT428 Academic AI Lab & Comparative Benchmark**")
        st.caption("Benchmark Approach 1 (Rule-Based FSM) vs Approach 2 (Semantic Embeddings) vs Proposed Hybrid Architecture with real-time confusion matrices and latency traces.")
    with col_lab_btn:
        st.page_link("pages/1_🔬_AI_Evaluation_&_Benchmarks.py", label="Open AI Benchmark Lab 🔬", icon="📊")


# ----------------- 2. QUICK RECEPTION ACTION EXPANDERS -----------------
quick_col1, quick_col2, quick_col3 = st.columns(3)

with quick_col1:
    with st.expander("➕ **Quick Walk-In Booking**", expanded=False):
        st.markdown("##### Direct Counter Walk-In")
        w_name = st.text_input("Customer Name:", key="w_name", placeholder="e.g. Suman Saha")
        w_phone = st.text_input("10-Digit Phone:", key="w_phone", placeholder="e.g. 9876543210")
        
        all_services = get_all_services()
        svc_options = {f"{s['id']} - {s['name']} (₹{int(s['price_inr'])})": s['id'] for s in all_services}
        w_svc = st.selectbox("Select Service:", list(svc_options.keys()), key="w_svc")

        # Station choice
        barber_choices = {
            "Auto-Assign First Available Station": "default",
            "Station 1": "B1",
            "Station 2": "B2"
        }
        w_chair = st.selectbox("Assign Station:", list(barber_choices.keys()), key="w_chair")

        w_time = st.text_input("Time Slot (HH:MM):", value=datetime.now().strftime("%H:%M"), key="w_time")

        if st.button("Confirm Walk-In & Seat Now ✂️", use_container_width=True, type="primary"):
            if not w_name.strip() or len(w_phone.strip()) < 10:
                st.error("Please provide both customer name and 10-digit mobile number.")
            else:
                svc_id = svc_options[w_svc]
                b_id = barber_choices[w_chair]
                send_action_update("walkin", {
                    "customer_name": w_name.strip(),
                    "phone": w_phone.strip(),
                    "service_id": svc_id,
                    "barber_id": b_id,
                    "date_str": today_str,
                    "time_str": w_time.strip()
                })
                st.success(f"Walk-in for {w_name} confirmed and queued!")
                time.sleep(1)
                st.rerun()

with quick_col2:
    with st.expander("📅 **Shop Closed / Holiday Manager**", expanded=False):
        st.markdown("##### Salon Availability Controller")
        if is_closed_today:
            st.error(f"⚠️ Salon is marked CLOSED for Today ({closed_reason})")
            if st.button("Re-Open Salon for Today 🟢", use_container_width=True):
                send_action_update("holiday", {"date_str": today_str, "is_closed": False})
                st.success("Salon re-opened for today!")
                time.sleep(1)
                st.rerun()
        else:
            st.success("🟢 Salon is currently OPEN for appointments today.")
            if st.button("Close Salon for Today 🔴", use_container_width=True):
                send_action_update("holiday", {"date_str": today_str, "is_closed": True, "reason": "Closed by Front Desk Manager"})
                st.warning("Salon marked closed for today! Bot will refuse new appointments.")
                time.sleep(1)
                st.rerun()

        st.divider()
        st.caption("Schedule a Future Closed Date / Holiday:")
        future_date = st.date_input("Select Date:", min_value=datetime.now().date(), key="f_date")
        f_reason = st.text_input("Reason:", placeholder="e.g. Festival, Deep Cleaning, Campus Maintenance", key="f_reason")
        if st.button("Set Date Closed", key="btn_close_date"):
            d_str = future_date.strftime("%Y-%m-%d")
            send_action_update("holiday", {"date_str": d_str, "is_closed": True, "reason": f_reason or "Scheduled Holiday"})
            st.success(f"Marked {d_str} as closed!")
            time.sleep(1)
            st.rerun()

        if holidays:
            st.markdown("###### Scheduled Closed Dates:")
            for h in holidays:
                h_c1, h_c2 = st.columns([3, 1])
                h_c1.caption(f"• **{h['date_str']}**: {h['reason']}")
                if h_c2.button("Remove ❌", key=f"del_h_{h['id']}"):
                    send_action_update("holiday", {"date_str": h['date_str'], "is_closed": False})
                    st.rerun()

with quick_col3:
    with st.expander("👥 **Station Operations & Daily Capacity (Station 1 & Station 2)**", expanded=False):
        st.markdown("##### Station Availability")
        st.caption("Controls concurrent booking capacity (1 vs 2 slots):")

        all_b = get_all_barbers()
        active_ids = [ab["id"] for ab in active_barbers]

        for b in all_b:
            b_is_active = b["id"] in active_ids
            b_station_label = "Station 1" if "1" in str(b["id"]) else "Station 2"
            status_text = "Active & On Duty ✅" if b_is_active else "Inactive / Off Duty 🏖️"

            c_info, c_btn = st.columns([3, 2])
            c_info.markdown(f"**🪑 {b_station_label}**<br><span style='font-size:0.8rem; color:#94A3B8;'>{status_text}</span>", unsafe_allow_html=True)
            
            toggle_label = "Set Inactive" if b_is_active else "Set Active"
            if c_btn.button(toggle_label, key=f"rost_{b['id']}"):
                send_action_update("roster", {
                    "date_str": today_str,
                    "barber_id": b["id"],
                    "is_active": not b_is_active
                })
                st.toast(f"Updated attendance for {b_station_label}!")
                time.sleep(0.5)
                st.rerun()

        st.divider()
        if active_barber_count == 2:
            st.success("🟢 **Full Capacity:** Both Stations Active (2 concurrent slots).")
        elif active_barber_count == 1:
            st.warning("🟡 **Half Capacity:** 1 Station Active (1 slot per time interval).")
        else:
            st.error("🔴 **Zero Capacity:** Both Stations inactive.")


st.divider()


# ----------------- 3. KPI STAT HIGHLIGHTS (PULSE CLINIC METRICS) -----------------
# Filter today's appointments
today_apps = [a for a in all_apps if a.get("appointment_date") == today_str]
today_booked_count = len([a for a in today_apps if a.get("status") == "BOOKED"])
today_in_service_count = len([a for a in today_apps if a.get("status") == "IN_SERVICE"])
today_completed_count = len([a for a in today_apps if a.get("status") == "COMPLETED"])
today_revenue = sum(float(a.get("price_inr", 0)) for a in today_apps if a.get("status") == "COMPLETED")
today_projected = sum(float(a.get("price_inr", 0)) for a in today_apps if a.get("status") in ["BOOKED", "IN_SERVICE", "COMPLETED"])

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    label="Today's Appointments",
    value=len(today_apps),
    delta=f"{today_booked_count} Upcoming · {len(all_apps)} Total Recorded"
)
m2.metric(
    label="In-Chair Right Now",
    value=today_in_service_count,
    delta=f"{active_barber_count} Active Chair Stations"
)
m3.metric(
    label="Completed Today",
    value=today_completed_count,
    delta=f"₹{int(today_revenue):,} Billed"
)
m4.metric(
    label="Today's Revenue",
    value=f"₹{int(today_revenue):,}",
    delta=f"₹{int(today_projected):,} Projected"
)

st.divider()


# ----------------- 4. DUAL-CHAIR STATION STATUS MONITOR -----------------
st.subheader("💈 Live Salon Stations (BH-5)")

st_col1, st_col2 = st.columns(2)

# Station 1
chair1_b = next((b for b in all_b if "B1" in b["id"] or "1" in b["name"]), all_b[0] if all_b else None)
chair1_active = chair1_b and chair1_b["id"] in active_ids if chair1_b else False
chair1_current = [a for a in today_apps if a.get("barber_id") == (chair1_b["id"] if chair1_b else "") and a.get("status") == "IN_SERVICE"]
chair1_next = [a for a in today_apps if a.get("barber_id") == (chair1_b["id"] if chair1_b else "") and a.get("status") == "BOOKED"]

with st_col1:
    with st.container(border=True):
        st.markdown("#### 🪑 Station 1")
        if not chair1_active:
            st.markdown('<span class="badge-cancelled">INACTIVE TODAY</span>', unsafe_allow_html=True)
            st.caption("No appointments assigned to Station 1 today.")
        elif chair1_current:
            cur = chair1_current[0]
            st.markdown('<span class="badge-inservice">IN-SERVICE NOW</span>', unsafe_allow_html=True)
            st.markdown(f"**Client:** {cur['customer_name']} (`{cur['phone']}`)")
            st.markdown(f"**Service:** ✂️ {cur['service_name']} (₹{int(cur['price_inr'])})")
            st.caption(f"Started at: {cur['start_time']} | Scheduled End: {cur.get('end_time', 'N/A')}")
            if st.button("Complete Service & Mark Paid ✅", key=f"ch1_comp_{cur['id']}", use_container_width=True):
                send_action_update("status", {"id": cur['id'], "status": "COMPLETED"})
                st.toast(f"Station 1 service completed for {cur['customer_name']}!")
                st.rerun()
        else:
            st.markdown('<span class="badge-completed">READY / AVAILABLE</span>', unsafe_allow_html=True)
            st.caption(f"Upcoming queue today: {len(chair1_next)} client(s)")
            if chair1_next:
                nxt = chair1_next[0]
                st.markdown(f"**Next:** {nxt['customer_name']} at **{nxt['start_time']}** ({nxt['service_name']})")
                if st.button("Seat Next Client ▶️", key=f"ch1_seat_{nxt['id']}", use_container_width=True):
                    send_action_update("status", {"id": nxt['id'], "status": "IN_SERVICE"})
                    st.rerun()

# Station 2
chair2_b = next((b for b in all_b if "B2" in b["id"] or "2" in b["name"]), all_b[1] if len(all_b) > 1 else None)
chair2_active = chair2_b and chair2_b["id"] in active_ids if chair2_b else False
chair2_current = [a for a in today_apps if a.get("barber_id") == (chair2_b["id"] if chair2_b else "") and a.get("status") == "IN_SERVICE"]
chair2_next = [a for a in today_apps if a.get("barber_id") == (chair2_b["id"] if chair2_b else "") and a.get("status") == "BOOKED"]

with st_col2:
    with st.container(border=True):
        st.markdown("#### 🪑 Station 2")
        if not chair2_active:
            st.markdown('<span class="badge-cancelled">INACTIVE TODAY</span>', unsafe_allow_html=True)
            st.caption("No appointments assigned to Station 2 today.")
        elif chair2_current:
            cur = chair2_current[0]
            st.markdown('<span class="badge-inservice">IN-SERVICE NOW</span>', unsafe_allow_html=True)
            st.markdown(f"**Client:** {cur['customer_name']} (`{cur['phone']}`)")
            st.markdown(f"**Service:** ✂️ {cur['service_name']} (₹{int(cur['price_inr'])})")
            st.caption(f"Started at: {cur['start_time']} | Scheduled End: {cur.get('end_time', 'N/A')}")
            if st.button("Complete Service & Mark Paid ✅", key=f"ch2_comp_{cur['id']}", use_container_width=True):
                send_action_update("status", {"id": cur['id'], "status": "COMPLETED"})
                st.toast(f"Station 2 service completed for {cur['customer_name']}!")
                st.rerun()
        else:
            st.markdown('<span class="badge-completed">READY / AVAILABLE</span>', unsafe_allow_html=True)
            st.caption(f"Upcoming queue today: {len(chair2_next)} client(s)")
            if chair2_next:
                nxt = chair2_next[0]
                st.markdown(f"**Next:** {nxt['customer_name']} at **{nxt['start_time']}** ({nxt['service_name']})")
                if st.button("Seat Next Client ▶️", key=f"ch2_seat_{nxt['id']}", use_container_width=True):
                    send_action_update("status", {"id": nxt['id'], "status": "IN_SERVICE"})
                    st.rerun()

st.divider()


# ----------------- 5. LIVE APPOINTMENT QUEUE TABLE (PULSE CLINIC PATIENT QUEUE) -----------------
st.subheader("📋 Customer Appointment Queue & Counter Dispatch")

f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 3, 2])
with f_col1:
    date_filter = st.selectbox("Date Scope:", ["Today Only", "All Upcoming & Past", "Tomorrow"], index=0)
with f_col2:
    status_filter = st.selectbox("Filter Status:", ["All", "BOOKED (Upcoming)", "IN_SERVICE", "COMPLETED", "CANCELLED"], index=0)
with f_col3:
    search_q = st.text_input("🔍 Search Client Name or Phone:", placeholder="e.g. Suman, 9876543210")
with f_col4:
    station_filter = st.selectbox("Filter Station:", ["All Stations", "Station 1 Only", "Station 2 Only"], index=0)

# Filter Logic
display_apps = all_apps

# 1. Date
if date_filter == "Today Only":
    display_apps = [a for a in display_apps if a.get("appointment_date") == today_str]
elif date_filter == "Tomorrow":
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    display_apps = [a for a in display_apps if a.get("appointment_date") == tomorrow_str]

# 2. Status
if "BOOKED" in status_filter:
    display_apps = [a for a in display_apps if a.get("status") == "BOOKED"]
elif status_filter != "All":
    display_apps = [a for a in display_apps if a.get("status") == status_filter]

# 3. Station
if station_filter == "Station 1 Only":
    display_apps = [a for a in display_apps if "1" in str(a.get("barber_id", "")) or "1" in str(a.get("barber_name", ""))]
elif station_filter == "Station 2 Only":
    display_apps = [a for a in display_apps if "2" in str(a.get("barber_id", "")) or "2" in str(a.get("barber_name", ""))]

# 4. Search
if search_q.strip():
    q = search_q.lower().strip()
    display_apps = [
        a for a in display_apps
        if q in str(a.get("customer_name", "")).lower() or q in str(a.get("phone", "")).lower() or q in str(a.get("service_name", "")).lower()
    ]

# Sort by Date & Time
display_apps = sorted(display_apps, key=lambda x: (x.get("appointment_date", ""), x.get("start_time", "")), reverse=True)

if display_apps:
    st.markdown(f"**Showing {len(display_apps)} appointment(s):**")
    for app in display_apps:
        with st.container(border=True):
            c_id, c_client, c_service, c_slot, c_price, c_status, c_act = st.columns([1, 3, 3, 3, 1.5, 2, 3])
            
            with c_id:
                st.markdown(f"**#{app['id']}**")

            with c_client:
                st.markdown(f"**{app['customer_name']}**")
                st.caption(f"📞 {app['phone']}")

            with c_service:
                st.markdown(f"✂️ **{app['service_name']}**")
                b_raw = str(app.get('barber_name', ''))
                b_disp = "Station 2" if ("2" in b_raw or "2" in str(app.get('barber_id', ''))) else "Station 1"
                st.caption(f"🪑 {b_disp}")

            with c_slot:
                st.markdown(f"📅 **{app['appointment_date']}**")
                st.caption(f"⏰ {app['start_time']} – {app.get('end_time', '')}")

            with c_price:
                st.markdown(f"**₹{int(app['price_inr'])}**")

            with c_status:
                st_val = app.get("status", "BOOKED")
                if st_val == "BOOKED":
                    st.markdown('<span class="badge-booked">BOOKED</span>', unsafe_allow_html=True)
                elif st_val == "IN_SERVICE":
                    st.markdown('<span class="badge-inservice">IN-CHAIR</span>', unsafe_allow_html=True)
                elif st_val == "COMPLETED":
                    st.markdown('<span class="badge-completed">COMPLETED</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-cancelled">CANCELLED</span>', unsafe_allow_html=True)

            with c_act:
                if st_val == "BOOKED":
                    btn_a1, btn_a2 = st.columns(2)
                    with btn_a1:
                        if st.button("Seat ▶️", key=f"seat_{app['id']}", use_container_width=True):
                            send_action_update("status", {"id": app['id'], "status": "IN_SERVICE"})
                            st.rerun()
                    with btn_a2:
                        if st.button("Cancel ❌", key=f"cnl_{app['id']}", use_container_width=True):
                            send_action_update("status", {"id": app['id'], "status": "CANCELLED"})
                            st.rerun()
                elif st_val == "IN_SERVICE":
                    if st.button("Complete & Billed ✅", key=f"done_{app['id']}", use_container_width=True, type="primary"):
                        send_action_update("status", {"id": app['id'], "status": "COMPLETED"})
                        st.toast(f"Booking #{app['id']} marked COMPLETED!")
                        st.rerun()
                else:
                    st.caption("Archived")
else:
    st.info("No matching appointments in the selected view.")

st.divider()


# ----------------- 6. ESCALATIONS & GRIEVANCES DESK -----------------
esc_col1, esc_col2 = st.columns(2)

with esc_col1:
    st.subheader("🚨 Staff Handover Requests")
    if pending_handovers:
        for ho in pending_handovers:
            with st.container(border=True):
                st.markdown(f"**Customer:** `{ho['customer_phone']}`")
                st.markdown(f"**Query:** *\"{ho['last_query']}\"*")
                st.caption(f"Reason: {ho['reason']}")
                if st.button("Mark Handled ✅", key=f"res_ho_{ho['id']}"):
                    send_action_update("handover", {"id": ho['id']})
                    st.rerun()
    else:
        st.success("✅ **Queue Clear:** No pending staff handover requests. AI Bot handling 100% of campus chats.")

with esc_col2:
    st.subheader("⚠️ Customer Feedback & Grievances")
    if open_complaints:
        for comp in open_complaints:
            with st.container(border=True):
                st.markdown(f"**Ticket #{comp['id']}** ({comp.get('severity', 'MEDIUM')} Severity)")
                st.markdown(f"**Client:** {comp.get('customer_name', 'Client')} (`{comp.get('phone', 'N/A')}`)")
                st.markdown(f"**Issue:** {comp.get('complaint_text', '')}")
                c_note = st.text_input("Resolution note:", key=f"note_{comp['id']}")
                if st.button("Resolve Ticket ✅", key=f"res_c_{comp['id']}"):
                    send_action_update("complaint", {"id": comp['id'], "notes": c_note or "Resolved at reception"})
                    st.rerun()
    else:
        st.success("✅ **Zero Grievances:** All customer tickets resolved. Customer satisfaction is 100%.")

st.divider()


# ----------------- 7. SALON COMPLETE RATE CARD -----------------
with st.expander("💈 **View Official Salon Rate Card (16 Services [S1-S16])**", expanded=False):
    services = get_all_services()
    if services:
        svc_display = [
            {
                "Code": s["id"],
                "Category": s["category"],
                "Service Name": s["name"],
                "Duration (mins)": s["duration_minutes"],
                "Rate (INR)": f"₹{int(s['price_inr'])}"
            }
            for s in services
        ]
        st.dataframe(svc_display, use_container_width=True)

# Auto-refresh loop (only runs when explicitly toggled on)
if auto_refresh:
    time.sleep(30)
    st.rerun()
