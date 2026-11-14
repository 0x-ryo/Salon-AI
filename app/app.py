"""
Razors-n-scissors Barber Salon — Front Desk Operations Portal
Inspired by "Pulse - Clinic Front Desk Dashboard" (Dribbble 27639583)
INT428 Artificial Intelligence Essentials | Group 13 | Student: Suman Saha (Reg: 12524973)

Front Desk Capabilities:
1. Executive KPI Summary Cards (Today's Bookings, Active Chairs, Revenue, Live Queue).
2. Store Closure & Scheduled Holiday Management (Open/Closed toggle, closure reason, holiday dates).
3. Dynamic Stylist Capacity Control (1 Stylist = 1 person/slot vs 2 Stylists = 2 persons/slot).
4. Live Front-Desk Queue & Schedule (Check-in, Complete, Cancel, WhatsApp Direct Link).
5. Quick Walk-In Booking Counter (Instant in-person booking on the spot).
6. Urgent Customer Escalation Queue (Option 11 WhatsApp Handover).
7. Customer Grievance Desk (Complaints with resolution tracking).
8. Official 16-Service Rate Card with [S1-S16] Catalog Notations.
"""

import os
import sys
import json
import time
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta

# Add paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

try:
    from salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS, TAGLINE
except Exception:
    try:
        from app.salon_config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS, TAGLINE
    except Exception:
        SALON_NAME = "Razors-n-scissors"
        PHONE_WHATSAPP = "+91 6284421638"
        ADDRESS = "BH-5, Lovely Professional University Campus, Phagwara, Punjab"
        OPERATING_HOURS = "Mon–Sun: 9:00 AM – 9:00 PM"
        TAGLINE = "Groom yourself at Razors-n-scissors"

from database.db import (
    init_db, get_all_services, get_all_barbers, get_all_appointments,
    get_all_complaints, resolve_complaint, get_handover_queue, resolve_handover,
    get_live_metrics, update_appointment_status, book_appointment,
    get_all_salon_settings, set_salon_setting, is_salon_closed_on
)

# Page Setup
st.set_page_config(
    page_title=f"{SALON_NAME} | Front Desk Operations",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize DB on load
init_db()

LIVE_API_BASE = os.environ.get("SALON_LIVE_API", "https://salon-ai-backend-6xdf.onrender.com")

# ─────────────────────────────────────────────────────────────────────────────
# PULSE CLINIC LUXURY FRONT-DESK STYLING (CSS)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container background */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Top Nav Brand Header */
    .pulse-navbar {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 18px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    .pulse-brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .pulse-logo-icon {
        width: 44px;
        height: 44px;
        background: #0F172A;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        color: #F8FAFC;
    }
    .pulse-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0;
        line-height: 1.2;
    }
    .pulse-subtitle {
        font-size: 0.82rem;
        color: #64748B;
        margin: 0;
    }

    /* Pulse Badges & Status Pills */
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.2px;
    }
    .pill-open {
        background-color: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .pill-closed {
        background-color: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .pill-capacity-2 {
        background-color: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    .pill-capacity-1 {
        background-color: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .dot-open { width: 8px; height: 8px; border-radius: 50%; background-color: #10B981; }
    .dot-closed { width: 8px; height: 8px; border-radius: 50%; background-color: #EF4444; }
    .dot-blue { width: 8px; height: 8px; border-radius: 50%; background-color: #3B82F6; }

    /* Pulse KPI Cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        position: relative;
        overflow: hidden;
    }
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .kpi-sub {
        font-size: 0.82rem;
        color: #475569;
        font-weight: 500;
    }

    /* Appointment Card (Pulse Front-Desk Row) */
    .app-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        transition: all 0.2s ease;
    }
    .app-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .avatar-circle {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: #F1F5F9;
        color: #0F172A;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
        border: 1px solid #E2E8F0;
    }
    .status-badge-booked {
        background: #ECFDF5;
        color: #047857;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-block;
    }
    .status-badge-completed {
        background: #F1F5F9;
        color: #475569;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-block;
    }
    .status-badge-cancelled {
        background: #FEF2F2;
        color: #B91C1C;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-block;
    }
    .chair-badge {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        color: #334155;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
    }

    /* Streamlit overrides for clean UI */
    div[data-testid="stMetric"] {
        display: none !important;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LIVE CLOUD & LOCAL DATA SYNC
# ─────────────────────────────────────────────────────────────────────────────
def fetch_frontdesk_data():
    """Fetches real-time front desk data from live cloud or local database fallback."""
    try:
        r_apps = requests.get(f"{LIVE_API_BASE}/api/appointments", timeout=2.0)
        r_met = requests.get(f"{LIVE_API_BASE}/api/metrics", timeout=2.0)
        r_ho = requests.get(f"{LIVE_API_BASE}/api/handovers", timeout=2.0)
        r_comp = requests.get(f"{LIVE_API_BASE}/api/complaints", timeout=2.0)
        r_set = requests.get(f"{LIVE_API_BASE}/api/settings", timeout=2.0)

        if r_apps.status_code == 200 and r_met.status_code == 200:
            return {
                "source": "LIVE_CLOUD",
                "appointments": r_apps.json(),
                "metrics": r_met.json(),
                "handovers": r_ho.json() if r_ho.status_code == 200 else [],
                "complaints": r_comp.json() if r_comp.status_code == 200 else [],
                "settings": r_set.json() if r_set.status_code == 200 else get_all_salon_settings()
            }
    except Exception:
        pass

    return {
        "source": "LOCAL_DB",
        "appointments": get_all_appointments(),
        "metrics": get_live_metrics(),
        "handovers": get_handover_queue(),
        "complaints": get_all_complaints(),
        "settings": get_all_salon_settings()
    }


def send_setting_update(key: str, value: str):
    """Updates salon operational setting locally and on live cloud backend."""
    set_salon_setting(key, value)
    try:
        requests.post(f"{LIVE_API_BASE}/api/action/settings", json={key: value}, timeout=1.5)
    except Exception:
        pass


def send_action(action_type: str, item_id: int, payload: dict = None):
    """Dispatches front-desk action update."""
    payload = payload or {}
    payload["id"] = item_id
    try:
        if action_type == "status":
            requests.post(f"{LIVE_API_BASE}/api/action/status", json=payload, timeout=1.5)
        elif action_type == "handover":
            requests.post(f"{LIVE_API_BASE}/api/action/handover", json=payload, timeout=1.5)
        elif action_type == "complaint":
            requests.post(f"{LIVE_API_BASE}/api/action/complaint", json=payload, timeout=1.5)
    except Exception:
        pass

    if action_type == "status":
        update_appointment_status(item_id, payload.get("status", "COMPLETED"))
    elif action_type == "handover":
        resolve_handover(item_id)
    elif action_type == "complaint":
        resolve_complaint(item_id, payload.get("notes", "Resolved at front desk"))


# Fetch current data
data = fetch_frontdesk_data()
settings = data["settings"]
appointments = data["appointments"]
metrics = data["metrics"]
handovers = [h for h in data["handovers"] if h.get("status") == "PENDING"]
complaints = [c for c in data["complaints"] if c.get("status") == "OPEN"]

is_closed = settings.get("is_closed", "0") == "1"
closure_reason = settings.get("closure_reason", "")
active_barbers = int(settings.get("active_barbers", "2"))
try:
    closed_dates_list = json.loads(settings.get("closed_dates", "[]"))
except Exception:
    closed_dates_list = []

# ─────────────────────────────────────────────────────────────────────────────
# 1. TOP NAVBAR (PULSE BRAND & LIVE STATUS)
# ─────────────────────────────────────────────────────────────────────────────
today_now = datetime.now()
today_str = today_now.strftime("%Y-%m-%d")
display_date = today_now.strftime("%A, %B %d, %Y")

st.markdown(f"""
<div class="pulse-navbar">
    <div class="pulse-brand">
        <div class="pulse-logo-icon">💈</div>
        <div>
            <h1 class="pulse-title">{SALON_NAME}</h1>
            <p class="pulse-subtitle">Campus Front-Desk Command Center · {ADDRESS}</p>
        </div>
    </div>
    <div style="display:flex; align-items:center; gap:10px;">
        {'<div class="pill pill-closed"><div class="dot-closed"></div>● Salon Closed</div>' if is_closed else '<div class="pill pill-open"><div class="dot-open"></div>● Salon Open</div>'}
        {'<div class="pill pill-capacity-2"><div class="dot-blue"></div>👥 2 Stylists Active (2/slot)</div>' if active_barbers == 2 else '<div class="pill pill-capacity-1">👤 1 Stylist Solo (1/slot)</div>'}
        <div style="font-size:0.82rem; color:#64748B; font-weight:600; padding-left:8px; border-left:1px solid #E2E8F0;">
            📅 {display_date}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. FRONT DESK QUICK CONTROL BAR (SHOP CLOSURE & STAFF CAPACITY)
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("⚙️ **Front Desk Operational Controls (Store Status & Stylist Capacity)**", expanded=False):
    ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([2, 2, 3])

    with ctrl_c1:
        st.markdown("##### 🏪 Store Status (Today)")
        new_closed_val = st.toggle("Shop Closed Today", value=is_closed, help="Toggle to immediately close the salon and stop accepting bookings for today.")
        if new_closed_val != is_closed:
            send_setting_update("is_closed", "1" if new_closed_val else "0")
            st.toast(f"Salon status updated: {'CLOSED' if new_closed_val else 'OPEN'}")
            st.rerun()

        reason_input = st.text_input("Closure Reason (if closed):", value=closure_reason, placeholder="e.g. Festival, Sunday Off, Campus Maintenance")
        if st.button("Save Closure Reason", key="save_reason", use_container_width=True):
            send_setting_update("closure_reason", reason_input.strip())
            st.toast("Closure reason saved!")
            st.rerun()

    with ctrl_c2:
        st.markdown("##### 👥 Stylist Staff Capacity")
        st.caption("How many barbers are working today?")
        cap_choice = st.radio(
            "Active Barbers on Duty:",
            options=[2, 1],
            index=0 if active_barbers == 2 else 1,
            format_func=lambda x: "👥 2 Barbers On Duty (2 bookings/slot · Chair 1 & 2)" if x == 2 else "👤 1 Barber Solo Duty (1 booking/slot · Chair 1 only)"
        )
        if cap_choice != active_barbers:
            send_setting_update("active_barbers", str(cap_choice))
            st.toast(f"Capacity set to {cap_choice} barber(s) per slot!")
            st.rerun()

    with ctrl_c3:
        st.markdown("##### 🗓️ Scheduled Holidays / Planned Closures")
        add_col, btn_col = st.columns([3, 2])
        with add_col:
            holiday_pick = st.date_input("Select Date to Close:", min_value=today_now.date(), value=today_now.date() + timedelta(days=1))
        with btn_col:
            st.write("")
            st.write("")
            if st.button("Add Closed Date ➕", use_container_width=True):
                h_str = holiday_pick.strftime("%Y-%m-%d")
                if h_str not in closed_dates_list:
                    closed_dates_list.append(h_str)
                    send_setting_update("closed_dates", json.dumps(closed_dates_list))
                    st.toast(f"Date {h_str} marked as CLOSED!")
                    st.rerun()

        if closed_dates_list:
            st.caption("Active Scheduled Holidays:")
            cols = st.columns(min(len(closed_dates_list), 4))
            for idx, h_date in enumerate(closed_dates_list):
                with cols[idx % 4]:
                    if st.button(f"❌ {h_date}", key=f"del_h_{h_date}", help=f"Remove closure for {h_date}"):
                        closed_dates_list.remove(h_date)
                        send_setting_update("closed_dates", json.dumps(closed_dates_list))
                        st.toast(f"Reopened {h_date}!")
                        st.rerun()
        else:
            st.caption("No planned holiday closures scheduled.")

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXECUTIVE KPI CARDS (PULSE STYLE)
# ─────────────────────────────────────────────────────────────────────────────
today_apps = [a for a in appointments if a.get("appointment_date") == today_str]
today_booked = len([a for a in today_apps if a.get("status") == "BOOKED"])
today_completed = len([a for a in today_apps if a.get("status") == "COMPLETED"])
today_cancelled = len([a for a in today_apps if a.get("status") == "CANCELLED"])
today_revenue = sum([float(a.get("price_inr", 0)) for a in today_apps if a.get("status") in ["BOOKED", "COMPLETED"]])
total_rev = metrics.get("total_revenue_inr", 0.0)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Today's Appointments</div>
        <div class="kpi-value">{len(today_apps)}</div>
        <div class="kpi-sub">
            <span style="color:#10B981; font-weight:700;">{today_booked} Booked</span> · 
            <span style="color:#64748B;">{today_completed} Done</span> · 
            <span style="color:#EF4444;">{today_cancelled} Off</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Stylist Chairs & Capacity</div>
        <div class="kpi-value">{'2 / 2' if active_barbers == 2 else '1 / 2'}</div>
        <div class="kpi-sub">
            {'<span style="color:#3B82F6; font-weight:700;">Chair 1 & Chair 2 Active</span>' if active_barbers == 2 else '<span style="color:#F59E0B; font-weight:700;">Chair 1 Solo Duty</span>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Today's Expected Revenue</div>
        <div class="kpi-value">₹{int(today_revenue):,}</div>
        <div class="kpi-sub">Total All-Time: <b>₹{int(total_rev):,}</b></div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    escalation_total = len(handovers) + len(complaints)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Front Desk Attention</div>
        <div class="kpi-value" style="color: {'#EF4444' if escalation_total > 0 else '#10B981'};">{escalation_total}</div>
        <div class="kpi-sub">
            {f'<span style="color:#EF4444; font-weight:700;">{len(handovers)} Staff Calls · {len(complaints)} Complaints</span>' if escalation_total > 0 else '<span style="color:#10B981; font-weight:700;">All Customer Desks Clear</span>'}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. URGENT ESCALATIONS / STAFF HANDOVERS (OPTION 11)
# ─────────────────────────────────────────────────────────────────────────────
if handovers or complaints:
    st.write("")
    alert_c1, alert_c2 = st.columns([1, 1])
    if handovers:
        with alert_c1:
            st.markdown("##### 🚨 Urgent WhatsApp Staff Handover Requests (Option 11)")
            for ho in handovers:
                with st.container(border=True):
                    st.markdown(f"**Customer:** `{ho['customer_phone']}`")
                    st.markdown(f"**Query:** *\"{ho['last_query']}\"*")
                    st.caption(f"Reason: {ho['reason']}")
                    if st.button("Mark Resolved ✅", key=f"ho_{ho['id']}", use_container_width=True):
                        send_action("handover", ho['id'])
                        st.toast("Handover resolved!")
                        st.rerun()
    if complaints:
        with alert_c2:
            st.markdown("##### ⚠️ Open Customer Complaints Desk")
            for cp in complaints:
                with st.container(border=True):
                    st.markdown(f"**Ticket #{cp['id']}** — Client: `{cp.get('phone', 'N/A')}`")
                    st.markdown(f"**Issue:** {cp.get('complaint_text', '')}")
                    res_note = st.text_input("Resolution note:", key=f"cn_{cp['id']}", placeholder="e.g. Free head wash offered")
                    if st.button("Close Ticket ✅", key=f"res_{cp['id']}", use_container_width=True):
                        send_action("complaint", cp['id'], {"notes": res_note})
                        st.toast("Complaint closed!")
                        st.rerun()

st.write("")

# ─────────────────────────────────────────────────────────────────────────────
# 5. FRONT DESK APPOINTMENT QUEUE & TIMELINE (PULSE HEART)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📋 Daily Schedule & Client Queue")

# Filter and Controls Bar
bar_c1, bar_c2, bar_c3, bar_c4 = st.columns([2, 2, 2, 2])

with bar_c1:
    selected_date = st.date_input("Select Schedule Date:", value=today_now.date(), key="queue_date")
    selected_date_str = selected_date.strftime("%Y-%m-%d")

with bar_c2:
    status_filter = st.selectbox("Status Filter:", ["All", "BOOKED", "COMPLETED", "CANCELLED"], index=0)

with bar_c3:
    search_query = st.text_input("Search Client / Phone:", placeholder="e.g. Suman, 9876543210")

with bar_c4:
    st.write("")
    st.write("")
    open_walkin = st.button("⚡ Book Walk-in Client", use_container_width=True, type="primary")

# Walk-in Booking Form Drawer
if open_walkin or st.session_state.get("show_walkin_form"):
    st.session_state.show_walkin_form = True
    with st.container(border=True):
        st.markdown("##### ⚡ Quick Front-Desk Walk-in Booking")
        w_c1, w_c2, w_c3, w_c4, w_c5 = st.columns(5)
        with w_c1:
            w_name = st.text_input("Client Name:", placeholder="e.g. Rahul Sharma")
        with w_c2:
            w_phone = st.text_input("Phone Number:", placeholder="e.g. 9876543210")
        with w_c3:
            all_svcs = get_all_services()
            svc_opts = {s["name"]: s["id"] for s in all_svcs}
            w_svc_name = st.selectbox("Service:", options=list(svc_opts.keys()))
            w_svc_id = svc_opts[w_svc_name]
        with w_c4:
            w_time = st.selectbox("Time Slot:", [
                "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "12:00", "12:30", "13:00", "14:00", "14:30", "15:00",
                "15:30", "16:00", "16:30", "17:00", "17:30", "18:00",
                "18:30", "19:00", "19:30", "20:00"
            ], index=4)
        with w_c5:
            st.write("")
            st.write("")
            sub_c1, sub_c2 = st.columns(2)
            with sub_c1:
                if st.button("Confirm ✅", key="submit_walkin", use_container_width=True):
                    if w_name and w_phone:
                        succ, msg, app_id = book_appointment(
                            customer_name=w_name.strip(),
                            phone=w_phone.strip(),
                            service_id=w_svc_id,
                            barber_id=None,
                            date_str=selected_date_str,
                            time_str=w_time
                        )
                        if succ:
                            st.toast(f"Walk-in #{app_id} Confirmed for {w_name}!")
                            st.session_state.show_walkin_form = False
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please provide Name and Phone.")
            with sub_c2:
                if st.button("Cancel", key="cancel_walkin", use_container_width=True):
                    st.session_state.show_walkin_form = False
                    st.rerun()

# Filter Appointments
date_filtered_apps = [a for a in appointments if a.get("appointment_date") == selected_date_str]
if status_filter != "All":
    date_filtered_apps = [a for a in date_filtered_apps if a.get("status") == status_filter]
if search_query.strip():
    q = search_query.lower().strip()
    date_filtered_apps = [
        a for a in date_filtered_apps
        if q in str(a.get("customer_name", "")).lower()
        or q in str(a.get("phone", "")).lower()
        or q in str(a.get("service_name", "")).lower()
        or q == str(a.get("id", ""))
    ]

# Sort by start_time ascending
date_filtered_apps.sort(key=lambda x: x.get("start_time", "00:00"))

# Check if salon is closed on this date
is_date_closed, close_reason = is_salon_closed_on(selected_date_str)
if is_date_closed:
    st.warning(f"⚠️ **Notice:** Razors-n-scissors is marked **CLOSED** on {selected_date_str} ({close_reason}). No online bookings are being accepted for this date.")

if date_filtered_apps:
    st.caption(f"Showing **{len(date_filtered_apps)}** appointment(s) for **{selected_date.strftime('%A, %b %d, %Y')}**:")

    for app in date_filtered_apps:
        app_id = app["id"]
        c_name = app.get("customer_name", "Valued Client")
        phone = app.get("phone", "")
        service = app.get("service_name", "Salon Service")
        start_t = app.get("start_time", "")
        end_t = app.get("end_time", "")
        price = int(float(app.get("price_inr", 0)))
        barber = app.get("barber_name", "Stylist Station")
        st_val = app.get("status", "BOOKED")

        # Customer Initials
        initials = "".join([part[0] for part in c_name.split() if part][:2]).upper() or "C"

        with st.container(border=True):
            r1, r2, r3, r4, r5, r6, r7 = st.columns([1.2, 2.8, 3, 2, 1.5, 1.8, 2.5])

            # Column 1: Time Slot
            with r1:
                st.markdown(f"**⏰ {start_t}**")
                st.caption(f"to {end_t}")

            # Column 2: Client Info
            with r2:
                st.markdown(f"**{c_name}**")
                clean_phone = phone.replace("+", "").replace("-", "").replace(" ", "")
                st.markdown(f"📞 [{phone}](https://wa.me/91{clean_phone[-10:] if len(clean_phone)>=10 else clean_phone})")

            # Column 3: Service Booked
            with r3:
                st.markdown(f"✂️ **{service}**")
                st.markdown(f"<span class='chair-badge'>{barber}</span>", unsafe_allow_html=True)

            # Column 4: Bill Amount
            with r4:
                st.markdown(f"**₹{price}**")
                st.caption("Cash / UPI")

            # Column 5: Status Pill
            with r5:
                if st_val == "BOOKED":
                    st.markdown("<span class='status-badge-booked'>● CONFIRMED</span>", unsafe_allow_html=True)
                elif st_val == "COMPLETED":
                    st.markdown("<span class='status-badge-completed'>● COMPLETED</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='status-badge-cancelled'>● CANCELLED</span>", unsafe_allow_html=True)

            # Column 6: Chair / Station
            with r6:
                st.markdown(f"**Booking #{app_id}**")
                st.caption("Verified Slot")

            # Column 7: Actions
            with r7:
                if st_val == "BOOKED":
                    act1, act2 = st.columns(2)
                    with act1:
                        if st.button("Done ✅", key=f"fin_{app_id}", use_container_width=True):
                            send_action("status", app_id, {"status": "COMPLETED"})
                            st.toast(f"Appointment #{app_id} marked COMPLETED!")
                            st.rerun()
                    with act2:
                        if st.button("Cancel ❌", key=f"can_{app_id}", use_container_width=True):
                            send_action("status", app_id, {"status": "CANCELLED"})
                            st.toast(f"Appointment #{app_id} cancelled.")
                            st.rerun()
                else:
                    st.caption("Archived")
else:
    st.info(f"No appointments scheduled for {selected_date.strftime('%A, %b %d, %Y')}. The salon queue is clear.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# 6. ANALYTICS & SERVICE BREAKDOWN
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📊 **Salon Business Analytics & Popular Services**", expanded=False):
    ana1, ana2 = st.columns(2)
    with ana1:
        st.markdown("##### 💈 Most Popular Grooming Services")
        top_services = metrics.get("top_services", [])
        if top_services:
            svc_names = [s["service"] for s in top_services]
            svc_counts = [s["count"] for s in top_services]
            fig_svc = px.bar(
                x=svc_counts,
                y=svc_names,
                orientation='h',
                labels={"x": "Bookings Count", "y": "Service"},
                color=svc_counts,
                color_continuous_scale="Teal"
            )
            fig_svc.update_layout(margin=dict(l=20, r=20, t=10, b=10), height=260)
            st.plotly_chart(fig_svc, use_container_width=True)
        else:
            st.caption("No booking analytics yet.")

    with ana2:
        st.markdown("##### 💰 Revenue Distribution")
        rev_labels = ["Active Bookings", "Completed Revenue"]
        rev_vals = [metrics.get("active_revenue_inr", 0), metrics.get("completed_revenue_inr", 0)]
        if sum(rev_vals) > 0:
            fig_pie = go.Figure(data=[go.Pie(labels=rev_labels, values=rev_vals, hole=0.5, marker_colors=["#3B82F6", "#10B981"])])
            fig_pie.update_layout(margin=dict(l=20, r=20, t=10, b=10), height=260)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.caption("No revenue recorded yet.")

# ─────────────────────────────────────────────────────────────────────────────
# 7. OFFICIAL 16-SERVICE RATE CARD (CATALOG CODES [S1] - [S16])
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📋 **Official 16-Service Salon Rate Card ([S1] to [S16])**", expanded=False):
    services = get_all_services()
    if services:
        svc_table = [
            {
                "Catalog Code": s["id"],
                "Category": s["category"],
                "Service Name": s["name"],
                "Duration": f"{s['duration_minutes']} mins",
                "Rate (INR)": f"₹{int(s['price_inr'])}"
            }
            for s in services
        ]
        st.dataframe(svc_table, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# 8. FOOTER NAVIGATION (ACADEMIC LAB LINK & CLOUD SYNC)
# ─────────────────────────────────────────────────────────────────────────────
st.write("")
footer_c1, footer_c2 = st.columns([3, 1])
with footer_c1:
    st.markdown(
        f"**{SALON_NAME}** · {ADDRESS} · WhatsApp Desk: `{PHONE_WHATSAPP}` · [Pair Cloud Bot]({LIVE_API_BASE}/pair)"
    )
with footer_c2:
    st.markdown(
        "🔬 **INT428 Academic Evaluation**  \n[Open AI Lab & Benchmarks →](http://localhost:8502)",
        help="Academic benchmark and comparative evaluation inspector for INT428 course submission."
    )
