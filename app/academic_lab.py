"""
Razors-n-scissors Salon — INT428 Academic Evaluation & AI Lab Inspector
INT428 Artificial Intelligence Essentials | Group 13 | Student: Suman Saha (Reg: 12524973)

Contains:
1. Empirical Benchmark across 30+ test queries comparing Approach 1 (Rule-Based FSM),
   Approach 2 (Dense Semantic Retrieval), and the Proposed Hybrid Model.
2. Latency & Accuracy Comparative Plotly Charts.
3. Interactive Explainability (XAI) Decision Trace Inspector for viva presentation.
"""

import os
import sys
import json
import time
import streamlit as st
import plotly.graph_objects as go

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from engine.hybrid_agent import HybridSalonAgent
from benchmark.evaluate import run_benchmark, RESULTS_PATH

st.set_page_config(
    page_title="INT428 AI Lab & Benchmark | Razors-n-scissors",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .academic-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        color: #F8FAFC;
        margin-bottom: 24px;
    }
    .badge-course {
        display: inline-block;
        background: rgba(59, 130, 246, 0.2);
        color: #60A5FA;
        border: 1px solid #3B82F6;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎓 Academic Submission")
    st.markdown("**Course:** INT428: Artificial Intelligence Essentials")
    st.markdown("**Group:** 13")
    st.markdown("**Student:** Suman Saha")
    st.markdown("**Reg No:** 12524973")
    st.divider()
    st.markdown("### 🔗 Quick Navigation")
    st.markdown("[← Return to Front-Desk Operations Portal](https://salon-ai-0x-ryo.streamlit.app/)")

st.markdown("""
<div class="academic-header">
    <div class="badge-course">INT428 · ARTIFICIAL INTELLIGENCE ESSENTIALS</div>
    <h1 style="margin: 0; font-size: 2rem; color: #FFFFFF;">🔬 AI Lab & Comparative Benchmark Inspector</h1>
    <p style="margin: 8px 0 0 0; color: #94A3B8; font-size: 1rem;">
        Empirical evaluation comparing <b>Approach 1 (Classical Rule-Based FSM)</b> vs. <b>Approach 2 (Dense Semantic Embeddings)</b> vs. <b>Proposed Hybrid Architecture</b>.
    </p>
</div>
""", unsafe_allow_html=True)

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
            marker_color=['#3B82F6', '#F59E0B', '#10B981']
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
            marker_color=['#3B82F6', '#F59E0B', '#10B981']
        )
    ])
    fig_lat.update_layout(yaxis=dict(range=[0, max(lat_values) * 1.3]), margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_lat, use_container_width=True)

st.divider()

# Interactive AI Query & Explainability Trace Inspector
st.subheader("🔍 Interactive AI Explainability (XAI) Decision Trace Inspector")
st.caption("Inspect real-time reasoning trace, fired rules, extracted slots, and latency for Unit II viva demonstration.")

sample_query = st.text_input(
    "Enter test customer query:",
    value="How much does a haircut and beard trim cost?",
    help="Type any query to inspect intent, confidence, and internal reasoning."
)

if st.button("Inspect AI Decision Trace 🔬", use_container_width=True):
    agent = HybridSalonAgent()
    ai_output = agent.handle_message(sample_query, engine_mode="Hybrid")

    st.markdown("**Bot Response:**")
    st.info(ai_output["response"])

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Engine Used", ai_output["engine_used"])
    col_m2.metric("Detected Intent", ai_output["intent"])
    col_m3.metric("Latency", f"{ai_output['latency_ms']} ms")

    st.markdown("**Explainability Trace (JSON):**")
    st.json(ai_output["trace"])
