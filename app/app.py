"""
Razors-n-scissors Barber Salon — Owner & Counter Management Portal
INT428 Course Project (Group 13 - Suman Saha | Reg: 12524973)

Customer Access Channels:
- Channel 1: WhatsApp Business Bot (Twilio Sandbox Webhook)
- Channel 2: Telegram Messenger Bot (@RazorsNScissorsBot)

Salon Operations Portal (Internal Counter Staff & Owner Only):
- Tab 1: Salon Manager & Counter Portal (Appointments, Revenue, Handover Queue, Complaints)
- Tab 2: INT428 AI Lab & Benchmark Inspector (Approach 1 vs 2 Evaluation & XAI Traces)
"""

import os
import sys
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Add project root to sys.path so modules resolve cleanly in all environments
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import SALON_NAME, PHONE_WHATSAPP, ADDRESS, OPERATING_HOURS, TAGLINE
from database.db import (
    init_db, get_all_services, get_all_barbers, get_all_appointments,
    get_all_complaints, resolve_complaint, get_handover_queue, resolve_handover,
    get_chat_logs
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

# Initialize DB on start
init_db()

# Initialize Session State
if "agent" not in st.session_state:
    st.session_state.agent = HybridSalonAgent()
if "engine_mode" not in st.session_state:
    st.session_state.engine_mode = "Hybrid (Production Agent)"

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
    st.markdown(f"**WhatsApp:** {PHONE_WHATSAPP}")
    st.markdown(f"**Motto:** *{TAGLINE}*")

    st.divider()
    st.markdown("### 📱 Customer Channels")
    st.info("Customers interact exclusively via **WhatsApp** and **Telegram**. This web portal is reserved for counter staff & salon management.")

    st.divider()
    st.subheader("⚙️ AI Engine Diagnostics")
    st.session_state.engine_mode = st.radio(
        "Active Architecture for Testing:",
        ["Hybrid (Production Agent)", "Approach 1 (Rule-Based FSM)", "Approach 2 (Semantic Retrieval)"],
        index=0,
        help="Select which AI core powers customer response generation."
    )

# ----------------- MAIN TABS -----------------
tab_owner, tab_ai_lab = st.tabs([
    "📊 Salon Manager & Counter Portal",
    "🔬 INT428 AI Lab & Comparative Benchmark"
])

# ================= TAB 1: SALON MANAGER PORTAL =================
with tab_owner:
    st.markdown("### 📊 Salon Owner & Counter Tablet Portal")
    st.caption(f"Real-time operational overview for {SALON_NAME} (BH-5, LPU Campus).")

    # Metric Cards
    all_apps = get_all_appointments()
    open_complaints = [c for c in get_all_complaints() if c["status"] == "OPEN"]
    pending_handovers = get_handover_queue()
    booked_count = sum(1 for a in all_apps if a["status"] == "BOOKED")
    today_revenue = sum(a["price_inr"] for a in all_apps if a["status"] == "BOOKED")

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Active Bookings", booked_count)
    m_col2.metric("Projected Revenue (INR)", f"₹{int(today_revenue):,}")
    m_col3.metric("Urgent Handover Requests", len(pending_handovers), delta=len(pending_handovers), delta_color="inverse")
    m_col4.metric("Unresolved Complaints", len(open_complaints), delta=len(open_complaints), delta_color="inverse")

    st.divider()

    # Section 1: Urgent Handover Queue
    st.subheader("🚨 Urgent Customer Handover Requests")
    if pending_handovers:
        for ho in pending_handovers:
            with st.container(border=True):
                h_c1, h_c2, h_c3 = st.columns([2, 5, 2])
                with h_c1:
                    st.markdown(f"**Customer:** {ho['customer_phone']}")
                    st.caption(f"Logged at: {ho['created_at']}")
                with h_c2:
                    st.markdown(f"**Query:** *\"{ho['last_query']}\"*")
                    st.markdown(f"**Reason:** `{ho['reason']}`")
                with h_c3:
                    if st.button("Mark Handled ✅", key=f"ho_{ho['id']}"):
                        resolve_handover(ho['id'])
                        st.toast(f"Handover #{ho['id']} resolved!")
                        st.rerun()
    else:
        st.success("✨ All customer inquiries are currently handled. No pending human escalations.")

    st.divider()

    # Section 2: Live Appointments Schedule
    st.subheader("📅 Live Appointments Schedule")
    if all_apps:
        display_apps = [
            {
                "ID": a["id"],
                "Client": a["customer_name"],
                "Phone": a["phone"],
                "Service": a["service_name"],
                "Date": a["appointment_date"],
                "Time": a["start_time"],
                "Amount (₹)": int(a["price_inr"]),
                "Status": a["status"]
            }
            for a in all_apps
        ]
        st.dataframe(display_apps, use_container_width=True)
    else:
        st.info("No appointments currently scheduled.")

    st.divider()

    # Section 3: Customer Feedback & Grievances Desk
    st.subheader("⚠️ Customer Feedback & Complaints Desk")
    complaints = get_all_complaints()
    if complaints:
        for comp in complaints:
            with st.expander(f"Ticket #{comp['id']} — {comp['severity']} Severity [{comp['status']}] - {comp['created_at']}"):
                st.markdown(f"**Customer:** {comp['customer_name']} ({comp['phone']})")
                st.markdown(f"**Grievance:** {comp['complaint_text']}")
                if comp["status"] == "OPEN":
                    res_note = st.text_input("Enter Resolution Note:", key=f"res_{comp['id']}")
                    if st.button("Resolve Ticket", key=f"btn_res_{comp['id']}"):
                        resolve_complaint(comp['id'], res_note or "Addressed with customer.")
                        st.toast("Ticket resolved successfully!")
                        st.rerun()
                else:
                    st.success(f"Resolved! Notes: {comp.get('resolution_notes', 'N/A')}")
    else:
        st.info("No complaints lodged yet.")

    st.divider()

    # Section 4: Live Service & Pricing Catalogue
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
        
        st.markdown(f"**Bot Response:**")
        st.info(ai_output["response"])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Engine Used", ai_output["engine_used"])
        col_m2.metric("Detected Intent", ai_output["intent"])
        col_m3.metric("Latency", f"{ai_output['latency_ms']} ms")
        
        st.markdown("**Explainability Trace (JSON):**")
        st.json(ai_output["trace"])
