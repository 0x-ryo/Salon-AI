"""
Razors-n-scissors Barber Salon — Owner & Counter Management Portal
INT428 Course Project (Group 13 - Suman Saha | Reg: 12524973)

Customer Access Channels:
- Channel 1: WhatsApp Business Bot
- Channel 2: Telegram Messenger Bot (@RazorsNScissorsBot)

Salon Operations Portal (Internal Counter Staff & Owner Only):
- Tab 1: Salon Manager & Counter Portal (Live Appointments, Revenue, Handover Queue, Complaints, Analytics)
- Tab 2: INT428 AI Lab & Benchmark Inspector (Approach 1 vs 2 Evaluation & XAI Traces)
"""

import os
import sys
import json
import time
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Add project root to sys.path so modules resolve cleanly in all environments
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
        PHONE_WHATSAPP = "+91 9877175449"
        ADDRESS = "BH-5, Lovely Professional University Campus, Phagwara, Punjab"
        OPERATING_HOURS = "Mon–Sun: 9:00 AM – 9:00 PM"
        TAGLINE = "Groom yourself at Razors-n-scissors"

from database.db import (
    init_db, get_all_services, get_all_barbers, get_all_appointments,
    get_all_complaints, resolve_complaint, get_handover_queue, resolve_handover,
    get_chat_logs, get_live_metrics, update_appointment_status
)
from engine.hybrid_agent import HybridSalonAgent
from benchmark.evaluate import run_benchmark, RESULTS_PATH

# Page Configuration
st.set_page_config(
    page_title=f"{SALON_NAME} | Salon Operations Portal",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Salon Luxury CSS Styling
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(20, 24, 33, 0.95), rgba(30, 36, 50, 0.95));
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(212, 175, 55, 0.7);
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #E0E0E0;
    }
    div[data-testid="stMetricValue"] {
        color: #D4AF37 !important;
        font-weight: 700;
    }
    .badge-booked {
        background-color: #1e3a8a;
        color: #93c5fd;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-completed {
        background-color: #064e3b;
        color: #6ee7b7;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-cancelled {
        background-color: #7f1d1d;
        color: #fca5a5;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-pill {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .status-live {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid #10B981;
    }
    .status-local {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid #F59E0B;
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB on start
init_db()

# Remote 24/7 Cloud API URL on Render (with Cloudflare fallback)
LIVE_API_BASE = os.environ.get("SALON_LIVE_API", "https://salon-ai-backend-6xdf.onrender.com")

def fetch_live_cloud_data():
    """
    Attempts to fetch real-time appointments and metrics from the live WhatsApp server.
    Falls back gracefully to local SQLite database if cloud tunnel is unreachable.
    """
    try:
        resp_apps = requests.get(f"{LIVE_API_BASE}/api/appointments", timeout=2.5)
        resp_metrics = requests.get(f"{LIVE_API_BASE}/api/metrics", timeout=2.5)
        resp_handovers = requests.get(f"{LIVE_API_BASE}/api/handovers", timeout=2.5)
        resp_complaints = requests.get(f"{LIVE_API_BASE}/api/complaints", timeout=2.5)

        if resp_apps.status_code == 200 and resp_metrics.status_code == 200:
            return {
                "source": "LIVE_CLOUD",
                "appointments": resp_apps.json(),
                "metrics": resp_metrics.json(),
                "handovers": resp_handovers.json() if resp_handovers.status_code == 200 else [],
                "complaints": resp_complaints.json() if resp_complaints.status_code == 200 else []
            }
    except Exception:
        pass

    # Local fallback
    apps = get_all_appointments()
    return {
        "source": "LOCAL_DB",
        "appointments": apps,
        "metrics": get_live_metrics(),
        "handovers": get_handover_queue(),
        "complaints": get_all_complaints()
    }


def send_action_update(action_type: str, item_id: int, payload: dict = None):
    """Sends action updates to live API or updates local SQLite DB."""
    payload = payload or {}
    payload["id"] = item_id

    # Try remote API first
    try:
        if action_type == "status":
            requests.post(f"{LIVE_API_BASE}/api/action/status", json=payload, timeout=2.0)
        elif action_type == "handover":
            requests.post(f"{LIVE_API_BASE}/api/action/handover", json=payload, timeout=2.0)
        elif action_type == "complaint":
            requests.post(f"{LIVE_API_BASE}/api/action/complaint", json=payload, timeout=2.0)
    except Exception:
        pass

    # Also apply locally
    if action_type == "status":
        update_appointment_status(item_id, payload.get("status", "COMPLETED"))
    elif action_type == "handover":
        resolve_handover(item_id)
    elif action_type == "complaint":
        resolve_complaint(item_id, payload.get("notes", "Resolved at counter"))


# Initialize Session State
if "agent" not in st.session_state:
    st.session_state.agent = HybridSalonAgent()
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = datetime.now().strftime("%H:%M:%S")

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.title(f"💈 {SALON_NAME}")
    st.caption("Salon Counter Portal & Operational Command Center")
    st.markdown("**Student:** Suman Saha (Reg: 12524973)")
    st.markdown("**Course:** INT428 · AI Foundations (Group 13)")

    st.divider()
    st.markdown("### 📍 Salon Details")
    st.markdown(f"**Address:** {ADDRESS}")
    st.markdown(f"**Hours:** {OPERATING_HOURS}")
    st.markdown(f"**WhatsApp Bot:** `+91 6284421638`")
    st.markdown(f"[🔗 **Pair WhatsApp Bot (24/7 Cloud)**]({LIVE_API_BASE}/pair)")
    st.markdown(f"**Motto:** *{TAGLINE}*")

    st.divider()
    st.markdown("### 📱 Real-Time Sync Settings")
    auto_refresh = st.toggle("⚡ Auto-Sync Every 5 Seconds", value=True)
    if st.button("🔄 Force Refresh Now", use_container_width=True):
        st.session_state.last_refresh_time = datetime.now().strftime("%H:%M:%S")
        st.rerun()

    st.caption(f"Last synced: {st.session_state.last_refresh_time}")

    st.divider()
    st.subheader("⚙️ AI Engine Diagnostics")
    st.session_state.engine_mode = st.radio(
        "Active Architecture for Testing:",
        ["Hybrid (Production Agent)", "Approach 1 (Rule-Based FSM)", "Approach 2 (Semantic Retrieval)"],
        index=0,
        help="Select which AI core powers customer response generation."
    )

# ----------------- LOAD LIVE DATA -----------------
live_data = fetch_live_cloud_data()
all_apps = live_data["appointments"]
metrics = live_data["metrics"]
pending_handovers = [h for h in live_data["handovers"] if h.get("status") == "PENDING"]
open_complaints = [c for c in live_data["complaints"] if c.get("status") == "OPEN"]

# ----------------- MAIN TABS -----------------
tab_owner, tab_ai_lab = st.tabs([
    "📊 Salon Manager & Counter Portal",
    "🔬 INT428 AI Lab & Comparative Benchmark"
])

# ================= TAB 1: SALON MANAGER PORTAL =================
with tab_owner:
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"### 📊 {SALON_NAME} — Salon Operations & Live Bookings")
        st.caption(f"Real-time counter tablet portal for {ADDRESS}.")
    with header_col2:
        if live_data["source"] == "LIVE_CLOUD":
            st.markdown('<div class="status-pill status-live">🟢 Live Cloud Engine Connected</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-pill status-local">🟡 Local Database Mode</div>', unsafe_allow_html=True)

    # Metric KPI Cards
    active_bookings = metrics.get("active_bookings", 0)
    total_rev = metrics.get("total_revenue_inr", 0.0)
    completed_bookings = metrics.get("completed_bookings", 0)
    handover_count = len(pending_handovers)
    complaint_count = len(open_complaints)

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Active Bookings", active_bookings, delta=f"{completed_bookings} Completed")
    m_col2.metric("Total Revenue (INR)", f"₹{int(total_rev):,}", delta=f"₹{int(metrics.get('active_revenue_inr', 0))} Booked")
    m_col3.metric("Urgent Handover Requests", handover_count, delta=handover_count, delta_color="inverse")
    m_col4.metric("Unresolved Grievances", complaint_count, delta=complaint_count, delta_color="inverse")

    st.divider()

    # Section 1: Urgent Escalations
    if pending_handovers:
        st.subheader("🚨 Urgent Customer Handover Requests")
        for ho in pending_handovers:
            with st.container(border=True):
                h_c1, h_c2, h_c3 = st.columns([2, 5, 2])
                with h_c1:
                    st.markdown(f"**Customer:** `{ho['customer_phone']}`")
                    st.caption(f"Logged at: {ho.get('created_at', 'Today')}")
                with h_c2:
                    st.markdown(f"**Customer Query:** *\"{ho['last_query']}\"*")
                    st.markdown(f"**Reason:** `{ho['reason']}`")
                with h_c3:
                    if st.button("Mark Handled ✅", key=f"ho_{ho['id']}", use_container_width=True):
                        send_action_update("handover", ho['id'])
                        st.toast(f"Handover #{ho['id']} resolved!")
                        st.rerun()
        st.divider()

    # Section 2: Live Appointments Schedule with Interactive Actions
    st.subheader("📅 Live Appointments Schedule & Customer Queue")

    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 2])
    with filter_col1:
        status_filter = st.selectbox("Filter Status:", ["All", "BOOKED", "COMPLETED", "CANCELLED"], index=0)
    with filter_col2:
        search_query = st.text_input("Search Client or Phone:", placeholder="e.g. Suman, 9877175449")
    with filter_col3:
        st.markdown(f"<div style='padding-top:28px; text-align:right;'><b>Total Records:</b> {len(all_apps)}</div>", unsafe_allow_html=True)

    filtered_apps = all_apps
    if status_filter != "All":
        filtered_apps = [a for a in filtered_apps if a.get("status") == status_filter]
    if search_query.strip():
        q = search_query.lower().strip()
        filtered_apps = [
            a for a in filtered_apps
            if q in str(a.get("customer_name", "")).lower() or q in str(a.get("phone", "")).lower() or q in str(a.get("service_name", "")).lower()
        ]

    if filtered_apps:
        # Display as rich interactive cards
        for app in filtered_apps:
            with st.container(border=True):
                c_id, c_client, c_service, c_slot, c_price, c_status, c_act = st.columns([1, 3, 3, 3, 2, 2, 3])
                with c_id:
                    st.markdown(f"**#{app['id']}**")
                with c_client:
                    st.markdown(f"**{app['customer_name']}**")
                    st.caption(f"📞 {app['phone']}")
                with c_service:
                    st.markdown(f"✂️ **{app['service_name']}**")
                    st.caption(f"Staff: {app.get('barber_name', 'Razors-n-scissors Staff')}")
                with c_slot:
                    st.markdown(f"📅 **{app['appointment_date']}**")
                    st.caption(f"⏰ {app['start_time']}")
                with c_price:
                    st.markdown(f"**₹{int(app['price_inr'])}**")
                with c_status:
                    st_val = app.get("status", "BOOKED")
                    if st_val == "BOOKED":
                        st.markdown('<span class="badge-booked">BOOKED</span>', unsafe_allow_html=True)
                    elif st_val == "COMPLETED":
                        st.markdown('<span class="badge-completed">COMPLETED</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-cancelled">CANCELLED</span>', unsafe_allow_html=True)
                with c_act:
                    if st_val == "BOOKED":
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.button("Complete ✅", key=f"comp_{app['id']}", use_container_width=True):
                                send_action_update("status", app['id'], {"status": "COMPLETED"})
                                st.toast(f"Appointment #{app['id']} marked COMPLETED!")
                                st.rerun()
                        with btn_c2:
                            if st.button("Cancel ❌", key=f"canc_{app['id']}", use_container_width=True):
                                send_action_update("status", app['id'], {"status": "CANCELLED"})
                                st.toast(f"Appointment #{app['id']} cancelled!")
                                st.rerun()
                    else:
                        st.caption("No actions needed")
    else:
        st.info("No matching appointments found.")

    st.divider()

    # Section 3: Visual Analytics
    st.subheader("📈 Salon Business & Service Analytics")
    ana_col1, ana_col2 = st.columns(2)

    with ana_col1:
        st.markdown("#### 💈 Appointments by Service")
        top_services = metrics.get("top_services", [])
        if top_services:
            svc_names = [s["service"] for s in top_services]
            svc_counts = [s["count"] for s in top_services]
            fig_svc = px.bar(
                x=svc_names,
                y=svc_counts,
                labels={"x": "Service Name", "y": "Bookings Count"},
                color=svc_counts,
                color_continuous_scale="Viridis"
            )
            fig_svc.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig_svc, use_container_width=True)
        else:
            st.caption("No service analytics available yet.")

    with ana_col2:
        st.markdown("#### 💰 Revenue Status Distribution")
        rev_labels = ["Active Booked Revenue", "Completed Revenue"]
        rev_vals = [metrics.get("active_revenue_inr", 0), metrics.get("completed_revenue_inr", 0)]
        if sum(rev_vals) > 0:
            fig_pie = go.Figure(data=[go.Pie(labels=rev_labels, values=rev_vals, hole=0.45, marker_colors=["#1E3A8A", "#10B981"])])
            fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.caption("No revenue recorded yet.")

    st.divider()

    # Section 4: Customer Complaints Desk
    st.subheader("⚠️ Customer Feedback & Complaints Desk")
    complaints = live_data["complaints"]
    if complaints:
        for comp in complaints:
            with st.expander(f"Ticket #{comp['id']} — {comp.get('severity', 'MEDIUM')} Severity [{comp.get('status', 'OPEN')}]"):
                st.markdown(f"**Customer:** {comp.get('customer_name', 'Client')} (`{comp.get('phone', 'N/A')}`)")
                st.markdown(f"**Grievance:** {comp.get('complaint_text', '')}")
                if comp.get("status") == "OPEN":
                    res_note = st.text_input("Enter Resolution Note:", key=f"res_{comp['id']}")
                    if st.button("Resolve Ticket", key=f"btn_res_{comp['id']}"):
                        send_action_update("complaint", comp['id'], {"notes": res_note or "Resolved by counter manager"})
                        st.toast("Ticket resolved successfully!")
                        st.rerun()
                else:
                    st.success(f"Resolved! Notes: {comp.get('resolution_notes', 'N/A')}")
    else:
        st.info("No complaints lodged yet. Salon satisfaction is 100%!")

    st.divider()

    # Section 5: Rate Card (16 Services)
    st.subheader("💈 Official Salon Rate Card (16 Services)")
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

# ================= TAB 2: AI LAB & BENCHMARK =================
with tab_ai_lab:
    st.markdown("### 🔬 INT428 AI Lab & Comparative Evaluation")
    st.caption("Empirical benchmark across 30 test cases comparing Approach 1 (Rule-Based), Approach 2 (Semantic), and Hybrid.")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_bench = st.button("⚡ Run Comparative Benchmark", use_container_width=True)

    if run_bench or not os.path.exists(RESULTS_PATH):
        with st.spinner("Executing 30+ test suite queries across Approach 1, Approach 2, and Hybrid..."):
            bench_data = run_benchmark()
    else:
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            bench_data = json.load(f)

    summary = bench_data["summary"]

    # Comparative Metric Cards
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Approach 1 (Rule-Based FSM)",
        f"{summary['overall_accuracy']['approach_1_rule_based']}% Acc",
        f"{summary['average_latency_ms']['approach_1_rule_based']} ms Latency"
    )
    c2.metric(
        "Approach 2 (Semantic Retrieval)",
        f"{summary['overall_accuracy']['approach_2_semantic']}% Acc",
        f"{summary['average_latency_ms']['approach_2_semantic']} ms Latency"
    )
    c3.metric(
        "Proposed Hybrid Agent",
        f"{summary['overall_accuracy']['proposed_hybrid']}% Acc",
        f"{summary['average_latency_ms']['proposed_hybrid']} ms Latency"
    )

    st.divider()

    # Visual Comparison Charts using Plotly Graph Objects
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### 🎯 Overall Intent & Task Accuracy (%)")
        arch_names = ["Approach 1 (Rule-Based)", "Approach 2 (Semantic)", "Proposed Hybrid Model"]
        acc_values = [
            summary['overall_accuracy']['approach_1_rule_based'],
            summary['overall_accuracy']['approach_2_semantic'],
            summary['overall_accuracy']['proposed_hybrid']
        ]
        fig_acc = go.Figure(data=[
            go.Bar(
                x=arch_names,
                y=acc_values,
                text=[f"{v}%" for v in acc_values],
                textposition='auto',
                marker_color=['#636EFA', '#EF553B', '#00CC96']
            )
        ])
        fig_acc.update_layout(yaxis=dict(range=[0, 110]), margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_acc, use_container_width=True)

    with chart_col2:
        st.markdown("#### ⚡ Average Response Latency (ms)")
        lat_values = [
            summary['average_latency_ms']['approach_1_rule_based'],
            summary['average_latency_ms']['approach_2_semantic'],
            summary['average_latency_ms']['proposed_hybrid']
        ]
        fig_lat = go.Figure(data=[
            go.Bar(
                x=arch_names,
                y=lat_values,
                text=[f"{v} ms" for v in lat_values],
                textposition='auto',
                marker_color=['#636EFA', '#EF553B', '#00CC96']
            )
        ])
        fig_lat.update_layout(yaxis=dict(range=[0, max(lat_values) * 1.3]), margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_lat, use_container_width=True)

    st.divider()

    # Interactive AI Query & Explainability Trace Inspector
    st.subheader("🔍 Interactive AI Explainability (XAI) Inspector")
    st.caption("Test how the AI processes any customer input and inspect the real-time reasoning trace.")

    sample_query = st.text_input(
        "Enter test customer query:",
        value="How much does a haircut and beard trim cost?",
        help="Type any query to inspect intent, confidence, and internal reasoning."
    )

    if st.button("Inspect AI Decision Trace 🔬", use_container_width=True):
        ai_output = st.session_state.agent.handle_message(sample_query, engine_mode="Hybrid")

        st.markdown("**Bot Response:**")
        st.info(ai_output["response"])

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Engine Used", ai_output["engine_used"])
        col_m2.metric("Detected Intent", ai_output["intent"])
        col_m3.metric("Latency", f"{ai_output['latency_ms']} ms")

        st.markdown("**Explainability Trace (JSON):**")
        st.json(ai_output["trace"])

# Auto-refresh loop for live counter updates
if auto_refresh:
    time.sleep(5)
    st.rerun()
