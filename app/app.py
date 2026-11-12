"""
Razors-n-scissors Barber Salon - Intelligent Customer Support & Management System
INT428 Course Project (Group 13 - Suman Saha)
Features:
- Tab 1: Salon Owner / Manager Dashboard (Appointments, Complaints, XAI)
- Tab 2: Salon Owner / Manager Tablet Portal (Appointments, Complaints, Handover Queue)
- Tab 3: AI Lab & Benchmark Inspector (Approach 1 vs Approach 2 Evaluation & XAI)
"""

import sys
import os
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from database.db import (
    init_db, get_all_services, get_all_barbers, get_all_appointments,
    get_all_complaints, resolve_complaint, get_handover_queue, resolve_handover,
    get_chat_logs
)
from engine.hybrid_agent import HybridSalonAgent
from benchmark.evaluate import run_benchmark, RESULTS_PATH

# Page Configuration
st.set_page_config(
    page_title="Razors-n-scissors | AI Support System",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB on start
init_db()

# Initialize Session State
if "agent" not in st.session_state:
    st.session_state.agent = HybridSalonAgent()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Welcome to **Razors-n-scissors**! I can help you check prices, find available slots with our master barbers, or book an appointment in seconds. How may I assist you today?",
            "trace": None,
            "engine": "System Greeting"
        }
    ]
if "engine_mode" not in st.session_state:
    st.session_state.engine_mode = "Hybrid (Production Agent)"

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.title("💈 Razors-n-scissors")
    st.caption("AI-Powered Customer Support & Operations")
    st.markdown("**Student:** Suman Saha (Reg: 12524973)")
    st.markdown("**Course:** INT428 · AI Foundations (Group 13)")
    
    st.divider()
    st.subheader("⚙️ AI Engine Settings")
    st.session_state.engine_mode = st.radio(
        "Active AI Architecture:",
        ["Hybrid (Production Agent)", "Approach 1 (Rule-Based FSM)", "Approach 2 (Semantic Retrieval)"],
        index=0,
        help="Select which AI core powers customer interactions."
    )
    
    st.divider()
    st.markdown("### 📍 Salon Information")
    st.markdown("**Hours:** Mon–Sun: 9:00 AM – 9:00 PM")
    st.markdown("**WhatsApp:** +91 9877175449")
    st.markdown("**Address:** BH-5, LPU Campus, Phagwara")

    if st.button("🔄 Reset Chat Session", use_container_width=True):
        st.session_state.agent.reset_session()
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Session reset! How can I help you today?",
                "trace": None,
                "engine": "System Reset"
            }
        ]
        st.rerun()

# ----------------- MAIN TABS -----------------
tab_customer, tab_owner, tab_ai_lab = st.tabs([
    "💬 Customer Support Chat",
    "📊 Salon Manager & Tablet Portal",
    "🔬 AI Lab & Comparative Benchmark (INT428)"
])

# ================= TAB 1: CUSTOMER CHAT =================
with tab_customer:
    st.markdown("### ✂️ Salon Customer Assistant")
    st.caption("Zero-friction customer chat for quick booking, service queries, and support.")

    # Quick Action Pills
    pills_col = st.columns(6)
    with pills_col[0]:
        if st.button("💈 Services & Rates", use_container_width=True):
            st.session_state.quick_query = "What services do you offer and what are the rates?"
    with pills_col[1]:
        if st.button("📅 Book Haircut", use_container_width=True):
            st.session_state.quick_query = "I want to book an appointment for Hair Cut"
    with pills_col[2]:
        if st.button("⏰ Opening Hours", use_container_width=True):
            st.session_state.quick_query = "What are your opening and closing timings?"
    with pills_col[3]:
        if st.button("✨ Salient Features", use_container_width=True):
            st.session_state.quick_query = "What are the salient features and hygiene standards?"
    with pills_col[4]:
        if st.button("❌ Cancel Booking", use_container_width=True):
            st.session_state.quick_query = "I want to cancel my appointment"
    with pills_col[5]:
        if st.button("🤝 Human Handover", use_container_width=True):
            st.session_state.quick_query = "Let me speak to the salon manager please"

    # Display Chat History
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="💈" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                
                # Show Explainability collapsible if trace is available
                if msg.get("trace"):
                    with st.expander("🔍 AI Explainability Trace (Why this answer?)", expanded=False):
                        st.json(msg["trace"])

    # Handle incoming query (from pills or input box)
    user_input = st.chat_input("Type your message here (e.g. 'Haircut price', 'Book haircut tomorrow at 4pm')...")
    
    if "quick_query" in st.session_state and st.session_state.quick_query:
        user_input = st.session_state.quick_query
        del st.session_state["quick_query"]

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Determine engine mode parameter
        engine_param = "Hybrid"
        if "Rule-Based" in st.session_state.engine_mode:
            engine_param = "Approach 1 (Rule-Based)"
        elif "Semantic" in st.session_state.engine_mode:
            engine_param = "Approach 2 (Semantic)"

        # Process with AI
        ai_output = st.session_state.agent.handle_message(user_input, engine_mode=engine_param)

        # Append assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_output["response"],
            "trace": ai_output["trace"],
            "engine": ai_output["engine_used"],
            "latency_ms": ai_output["latency_ms"]
        })
        st.rerun()

# ================= TAB 2: SALON MANAGER PORTAL =================
with tab_owner:
    st.markdown("### 📊 Salon Owner & Counter Tablet Portal")
    st.caption("Live control center for barbers, appointments, customer grievances, and human escalations.")

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

    # Section 1: Human Handover Escalation Queue
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

    # Section 2: Appointments Calendar & Management
    st.subheader("📅 Live Appointments Schedule")
    if all_apps:
        display_apps = [
            {
                "ID": a["id"],
                "Client": a["customer_name"],
                "Phone": a["phone"],
                "Service": a["service_name"],
                "Barber": a["barber_name"],
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

    # Section 3: Customer Complaints Desk
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

# ================= TAB 3: AI LAB & EVALUATION =================
with tab_ai_lab:
    st.markdown("### 🔬 AI Lab & Comparative Evaluation (INT428 Course Assessment)")
    st.caption("Demonstrating empirical superiority, explainability, and Responsible AI compliance.")

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
                marker_color=['#AB63FA', '#FFA15A', '#19D3F3']
            )
        ])
        fig_lat.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_lat, use_container_width=True)

    # Detailed Benchmark Breakdown Table
    st.markdown("#### 📋 Detailed Benchmark Query Log & Decisions")
    details = bench_data["detailed_results"]
    display_details = [
        {
            "ID": d["id"],
            "Category": d["category"],
            "User Query": d["query"],
            "Rule Intent": d["rule_intent"],
            "Rule Match?": "✅" if d["rule_success"] else "❌",
            "Sem Confidence": f"{d['sem_confidence']:.2f}",
            "Sem Match?": "✅" if d["sem_success"] else "❌",
            "Hybrid Intent": d["hyb_intent"]
        }
        for d in details
    ]
    st.dataframe(display_details, use_container_width=True)

    # Conversation Audit Trail (INT428 Rubric Requirement 7)
    st.divider()
    st.markdown("#### 📜 Live Conversation Audit & PII-Redacted Logs")
    logs = get_chat_logs(20)
    if logs:
        st.dataframe(logs, use_container_width=True)
    else:
        st.caption("No chat audit logs yet. Start chatting in Tab 1!")
