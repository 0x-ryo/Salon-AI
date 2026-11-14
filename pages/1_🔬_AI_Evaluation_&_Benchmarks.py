"""
Razors-n-scissors — Academic AI Lab & Comparative Benchmark Inspector
Course: INT428 · Artificial Intelligence Essentials (Group 13 - Suman Saha | Reg: 12524973)

Provides empirical evaluation comparing:
- Approach 1: Classical Rule-Based AI Engine & Finite State Machine (FSM)
- Approach 2: Dense Semantic Embeddings & Cosine Similarity Knowledge Retrieval
- Proposed Hybrid Architecture with DPDP Guardrails & Real-Time Orchestration
"""

import os
import sys
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Resolve project paths
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PAGE_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from salon_config import SALON_NAME
except Exception:
    SALON_NAME = "Razors-n-scissors"

from engine.hybrid_agent import HybridSalonAgent
from benchmark.evaluate import run_benchmark, RESULTS_PATH

st.set_page_config(
    page_title=f"{SALON_NAME} | AI Lab & Benchmarks",
    page_icon="🔬",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid rgba(79, 70, 229, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
    }
    div[data-testid="stMetricValue"] {
        color: #818CF8 !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔬 INT428 AI Lab & Comparative Benchmark")
st.caption(f"Empirical evaluation & Explainable AI (XAI) verification for {SALON_NAME} AI Architecture.")
st.markdown("**Student:** Suman Saha (Reg: 12524973) | **Course:** INT428: Artificial Intelligence Essentials (Group 13)")

st.divider()

col_btn, col_info = st.columns([1, 3])
with col_btn:
    run_bench = st.button("⚡ Run Full Benchmark Suite", use_container_width=True)
with col_info:
    st.info("Benchmarks 30+ empirical test cases assessing Intent Accuracy, Slot Extraction, Execution Latency, and DPDP Guardrail Compliance.")

if run_bench or not os.path.exists(RESULTS_PATH):
    with st.spinner("Executing test suite queries across Approach 1, Approach 2, and Hybrid..."):
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

# Charts
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
            marker_color=['#636EFA', '#EF553B', '#10B981']
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
            marker_color=['#636EFA', '#EF553B', '#10B981']
        )
    ])
    fig_lat.update_layout(yaxis=dict(range=[0, max(lat_values) * 1.3]), margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_lat, use_container_width=True)

st.divider()

# Interactive AI Query & Explainability Trace Inspector
st.subheader("🔍 Interactive AI Explainability (XAI) Inspector")
st.caption("Live decision audit: test arbitrary customer input and inspect internal slot filling and rule firing.")

if "lab_agent" not in st.session_state:
    st.session_state.lab_agent = HybridSalonAgent()

sample_query = st.text_input(
    "Enter test customer query:",
    value="How much does a haircut and beard trim cost?",
    help="Type any query to inspect intent, confidence, and internal reasoning."
)

if st.button("Inspect AI Decision Trace 🔬", use_container_width=True):
    ai_output = st.session_state.lab_agent.handle_message(sample_query, engine_mode="Hybrid")

    st.markdown("**Generated Response:**")
    st.info(ai_output["response"])

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Engine Dispatched", ai_output["engine_used"])
    col_m2.metric("Detected Intent", ai_output["intent"])
    col_m3.metric("Execution Latency", f"{ai_output['latency_ms']} ms")

    st.markdown("**Explainability Trace (JSON):**")
    st.json(ai_output["trace"])
