# Customer Support Chatbot & Operational Management Portal for a Real Small Business
### 💈 Razors-n-scissors Barber Salon (BH-5, LPU Campus) · 24/7 Intelligent AI Operations & WhatsApp Bot

[![Course](https://img.shields.io/badge/Course-INT428%20AI%20Essentials-blue.svg)](https://www.lpu.in)
[![Group](https://img.shields.io/badge/Group-13-green.svg)]()
[![Student](https://img.shields.io/badge/Student-Suman%20Saha%20(12524973)-orange.svg)]()
[![Python](https://img.shields.io/badge/Python-3.12-yellow.svg)]()
[![Cloud Gateway](https://img.shields.io/badge/Render%20Cloud-24%2F7%20Online-brightgreen.svg)](https://salon-ai-backend-6xdf.onrender.com)
[![Streamlit Cloud](https://img.shields.io/badge/Streamlit%20Cloud-Live%20Dashboard-FF4B4B.svg)](https://salon-ai-0x-ryo.streamlit.app/)
[![Zero-Cost](https://img.shields.io/badge/Cost-%E2%82%B90.00%20(100%25%20Free)-success.svg)]()

> **Continuous Assessment (CA) Project**  
> **Course:** INT428: Artificial Intelligence Essentials · Lovely Professional University  
> **Allocated Topic (Group 13):** *Customer Support Chatbot & Operational Management Portal for a Real Small Business (Salon / Barber Shop)*  
> **Target Enterprise:** **Razors-n-scissors Barber Salon**, BH-5, Lovely Professional University Campus, Phagwara, Punjab.

---

## 🌐 Live Cloud Deployments & Access Points

| Service | Access Link | Description |
| :--- | :--- | :--- |
| **Live Operations Portal** | [salon-ai-0x-ryo.streamlit.app](https://salon-ai-0x-ryo.streamlit.app/) | Streamlit Cloud live counter dashboard, appointment scheduler, revenue analytics, and INT428 AI Lab Inspector. |
| **24/7 Cloud Bot Gateway** | [salon-ai-backend-6xdf.onrender.com](https://salon-ai-backend-6xdf.onrender.com) | Python FastAPI + Neonize WebSocket cloud engine on Render (runs 24/7 without requiring a laptop). |
| **WhatsApp Device Pairing** | [Pairing Screen (`/pair`)](https://salon-ai-backend-6xdf.onrender.com/pair) | Real-time multi-device pairing interface for WhatsApp salon bot. |
| **Target Salon WhatsApp** | **`+91 XXXXX-XXXXX`** *(Protected · Configured via `WA_TARGET_PHONE`)* | Real salon contact number for multi-turn appointment bookings, inquiries, and grievances. |
| **Persistent Storage** | **Render PostgreSQL (`salon-db`)** | Managed relational cloud database preserving multi-device session keys permanently across restarts. |

---

## 📌 Executive Summary

Barber salons and grooming parlors experience continuous operational interruptions: stylists must drop shears mid-haircut to answer repetitive telephone calls asking for rates, wait times, or booking slots. After-hours inquiries (8:30 PM to 9:00 AM) are routinely missed, resulting in lost bookings to competitors.

This project delivers an enterprise-grade, **zero-cost, 24/7 cloud-native AI customer support and operational portal** custom-built for **Razors-n-scissors Salon**:

1. **Zero Customer Friction (Direct WhatsApp Connectivity):** Customers interact directly through WhatsApp using natural language without downloading any app or joining restrictive developer sandboxes.
2. **24/7 Autonomous Cloud Execution (Zero Laptop Dependency):** Deployed on Render with native WebSocket bindings (`neonize`) and PostgreSQL persistent storage, allowing the bot to run continuously even when the owner's computer is turned off.
3. **Dual AI Implementation (INT428 Academic Mandate):** Formally implements and benchmarks **Approach 1 (Classical Rule-Based FSM Slot-Filler)** vs. **Approach 2 (Dense Sentence-Transformers Semantic Retrieval)** alongside a **Hybrid Production Agent**.
4. **Live Real-Time Dashboard Sync:** Streamlit Cloud dashboard synchronizes appointments, metrics, revenue KPIs, and staff escalation queues from the Render cloud backend every 5 seconds.
5. **Zero Hallucination Guarantee & Responsible AI:** Strict grounding in verified relational tables and JSON knowledge bases, DPDP Act PII masking, and explicit medical safety boundary filters (refusing scalp disorder diagnoses).
6. **Multi-Service & Interval Conflict Prevention:** Automatically aggregates durations and combo pricing for multi-service requests (`1 and 2`) while strictly blocking chair overlap collisions ($\text{start}_1 < \text{end}_2 \land \text{end}_1 > \text{start}_2$).

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph WhatsApp_Channel ["Customer WhatsApp Channel - 24/7 Cloud"]
        CLIENT["Customer Mobile WhatsApp - Direct Chat with Salon"]
        WSS["WhatsApp Multi-Device Gateway - Pure Python Neonize / WebSockets"]
    end

    subgraph Cloud_Backend ["Render 24/7 Cloud Backend - salon-ai-backend"]
        FASTAPI["FastAPI Webhook and REST APIs - /health, /pair, /api/metrics"]
        
        subgraph AI_Core ["Hybrid Salon AI Core - INT428"]
            GUARD["Responsible AI Guardrails - DPDP PII Redaction, Medical Safety"]
            ROUTER{"Intent Router"}
            APP1["Approach 1: Classical AI - Regex and FSM Dialog Tracker"]
            APP2["Approach 2: Modern AI - Sentence-Transformers MiniLM"]
            XAI["Explainability Trace Engine - Confidence and Decision Logs"]
        end
        
        SQLITE[("Local SQLite Cache - salon.db WAL Mode")]
    end

    subgraph Cloud_Storage ["Cloud Persistence Layer"]
        PG[("Render PostgreSQL - salon-db Persistent Session Keys")]
    end

    subgraph Operations_Portal ["Live Salon Operations Command Center"]
        DASH["Streamlit Cloud Dashboard - 5s Auto Sync Luxury Gold UI"]
    end

    CLIENT <-->|E2EE Messages| WSS
    WSS <-->|Native Python Bindings| FASTAPI
    FASTAPI --> GUARD
    GUARD --> ROUTER
    ROUTER -->|Transactional Bookings| APP1
    ROUTER -->|FAQs and Services| APP2
    APP1 <--> SQLITE
    APP2 <--> SQLITE
    APP1 --> XAI
    APP2 --> XAI
    XAI --> FASTAPI
    WSS <-->|Session Sync| PG
    FASTAPI <-->|REST JSON Sync - 5s Polling| DASH
```

---

## 📊 Empirical Evaluation Benchmark (30 Real-World Test Cases)

| Metric | Approach 1 (Rule-Based FSM) | Approach 2 (Semantic Retrieval) | Proposed Hybrid Production Model |
| :--- | :---: | :---: | :---: |
| **Overall Intent Accuracy** | 56.7% | 76.7% | **100.0%** |
| **Paraphrase Resilience** | 40.0% | **100.0%** | **100.0%** |
| **Average Response Latency** | **1.70 ms** | 8.28 ms | **9.01 ms** |
| **Safety Guardrail Refusal Rate** | 40.0% | 60.0% | **100.0%** |
| **Hallucination Rate** | **0.0%** | **0.0%** | **0.0%** |
| **Double-Booking Rate** | **0.0%** | N/A | **0.0%** |
| **Automated Unit & Integration Tests** | 19 / 19 Passed | 19 / 19 Passed | **19 / 19 Passed (100%)** |

---

## ✨ Core Features & Dialogue Management

### 1. Interactive Luxury Master Menu
When a customer initiates a conversation (`Hi` or `Menu`), the bot delivers a sleek, uncluttered card menu:
* `1` ➔ **Hair Cut** — ₹100 _(20 min)_
* `2` ➔ **Beard Trim / Shave** — ₹50 _(15 min)_
* `3` ➔ **Cut + Beard Combo** — ₹140 _(30 min)_
* `4` ➔ **Head Wash** — ₹50 _(15 min)_
* `5` ➔ **Hair Spa / Keratin** — ₹400 _(45 min)_
* `6` ➔ **D-Tan Cleaner / Facial** — ₹300 _(25 min)_
* `7` ➔ **Hair Colour** — ₹450 _(40 min)_
* `8` ➔ **Full Price List (All 16 Services)**
* `9` ➔ **Salon Timings & Location (BH-5, LPU)**
* `10` ➔ **Check / Cancel Booking or Connect with Staff**

### 2. Multi-Service Selection & Combo Packaging
Customers can choose multiple services in a single message (e.g. `1 and 2` or `Haircut and beard trim`). The engine computes combined duration (35 mins) and combo rates (₹140), reserving the styling chair for the entire continuous block.

### 3. Natural Language Comprehension
Customers do not need to memorize numbers. The hybrid router handles conversational input:
* *"Book haircut and beard trim tomorrow at 4pm"* ➔ **One-Shot Reservation**
* *"What time do you close on Sundays?"* ➔ **Knowledge Base Retrieval**
* *"My scalp has severe red infection, prescribe an antibiotic ointment"* ➔ **Medical Scope Refusal** (safely directs client to a qualified dermatologist and refuses medical prescriptions).

### 4. Human Staff Escalation & Grievances Desk
If an inquiry requires personal attention or the customer expresses dissatisfaction, the bot automatically registers a ticket in the **Human Handover Queue** or **Complaints Desk**, instantly visible to counter staff on the Streamlit dashboard.

---

## 💈 Pulse Clinic Front-Desk Reception Portal & Station Operations

The salon's front-desk interface is designed with a high-end, clean clinical reception workflow inspired by **Pulse Clinic Front Desk**:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 💈 Razors-n-scissors · Front Desk Reception   [🟢 Salon Open · 2 Stations Active] [● Cloud Sync] │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🔬 INT428 Academic AI Lab & Model Benchmark                     [Open AI Benchmark Lab 🔬 📊]   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ➕ Quick Walk-In Booking     │ 📅 Shop Closed / Holiday Manager │ 👥 Station Operations & Rosters│
├──────────────────────────────┼──────────────────────────────────┼────────────────────────────────┤
│ [Today: 18 Appts]            │ [In-Chair: 1 Client]             │ [Completed: 14] [₹1,850 Rev]   │
├──────────────────────────────┴──────────────────────────────────┴────────────────────────────────┤
│ 🪑 Station 1: IN-SERVICE NOW (Suman - Hair Cut)     │ 🪑 Station 2: READY / AVAILABLE           │
│    [Complete Service & Mark Paid ✅]                │    Next: Rahul (16:30) [Seat Client ▶️]   │
├─────────────────────────────────────────────────────┴────────────────────────────────────────────┤
│ 📋 Customer Appointment Queue & Counter Dispatch (Filters: Station 1 / Station 2 / All Dates)    │
│ 🚨 Staff Handover Requests (0 Pending)              │ ⚠️ Customer Feedback Desk (0 Open)         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Dual-Station Allocation (Station 1 & Station 2)
* **Zero Barber Personal Names:** In accordance with salon management practices, stylists operate under designated stations (**Station 1** and **Station 2**). This preserves stylist privacy and enables smooth shift rotations without customer confusion.
* **Live In-Chair Monitors:** The dashboard displays real-time occupancy for both stations, displaying current client name, phone number, service duration, scheduled end time, and one-click counter completion.

### 2. Dynamic Daily Capacity (1 vs 2 Concurrent Bookings)
* **Full Attendance (Both Active):** When both Station 1 and Station 2 are marked on duty, each 30-minute booking slot accepts up to **2 concurrent appointments**.
* **Solo Attendance (1 Active):** If one stylist is off or on leave, the system automatically constrains capacity to **1 booking per slot**, preventing queue overbooking.
* **Full Inactive (Both Off):** All appointment slots are automatically suspended.

### 3. Salon Closure & Holiday Management
* Front-desk managers can instantly mark the salon as **Closed for Today** or schedule **Future Closed Dates / Holidays** (e.g., campus maintenance, festival closures).
* The AI Bot reads this status in real-time, immediately refusing new appointments for those dates while guiding clients to next available working days.

### 4. Zero Screen Flickering & Stable Counter Display
* **Anti-Flicker Architecture:** The full-page automatic refresh loop (`st.rerun()`) is disabled by default, preventing the entire DOM and the Staff Handover alert box from blinking or flashing.
* **On-Demand Counter Sync:** Receptionists use the prominent `🔄 Refresh Counter Data` button for instant, zero-flicker live sync.
* **Gentle Auto-Refresh Option:** When background polling is toggled on, it runs on a calm 30-second interval rather than an aggressive 5-second loop.

---

## 🔬 Finding & Navigating the INT428 Academic AI Lab

The academic evaluation suite is permanently integrated and easily accessible through two prominent discovery paths:

1. **Top Reception Callout Banner:** Right below the front-desk header on the main dashboard, an interactive callout banner provides a direct one-click button:  
   👉 **`Open AI Benchmark Lab 🔬`**
2. **Streamlit Multi-Page Sidebar:** Located in the left navigation sidebar under `pages/1_🔬_AI_Evaluation_&_Benchmarks.py`.

### What's Inside the AI Lab:
* **Real-Time Confusion Matrix:** Live classification performance comparing Approach 1 (Rules/FSM), Approach 2 (MiniLM Semantic Embeddings), and the Proposed Hybrid Architecture.
* **Empirical Metric Radar:** Side-by-side comparison of Precision, Recall, F1-Score, and Latency (ms).
* **Interactive Cosine Similarity Explorer:** Adjustable confidence threshold sliders ($\tau \in [0.5, 0.9]$) with live semantic distance visualizations.
* **Transparent XAI Audit Trail:** Step-by-step diagnostic traces showing regex rule matches, embedding similarity scores, and fallback decisions.

---

## 💾 Permanent Data Persistence Guarantee

A common operational concern for business owners is data permanence. In this platform, **100% of salon data is stored permanently**:

| Data Category | Stored Details | Storage Engine | Durability Guarantee |
| :--- | :--- | :--- | :--- |
| **Appointments** | Customer Name, Phone, Service, Station (1 or 2), Date, Slot, Price, Status (`BOOKED`, `IN_SERVICE`, `COMPLETED`, `CANCELLED`) | SQLite WAL Cache + Cloud Sync | Permanent · Survives restarts |
| **Grievances & Complaints** | Client Name, Phone, Issue Description, Severity Level, Resolution Notes, Status (`OPEN`, `RESOLVED`) | SQLite Relational DB | Permanent · Zero data loss |
| **Staff Handovers** | Phone Number, Customer Query Context, Escalation Reason, Status (`PENDING`, `HANDLED`), Timestamps | SQLite Relational DB | Permanent · Counter-trackable |
| **Salon Holidays** | Closure Dates (`YYYY-MM-DD`), Reason for Closure, Created Timestamp | SQLite Relational DB | Permanent · Active calendar |
| **Station Rosters** | Station ID (`B1`/`B2`), Active Status ($1/0$), Date String | SQLite Relational DB | Permanent · Dynamic capacity |
| **Conversation Logs** | Session ID, User Input, Bot Response, Detected Intent, Confidence, Engine Used, Latency | SQLite Relational DB | Permanent · Audit compliant |

* **SQLite Write-Ahead Logging (WAL Mode):** Configured with `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000` for immediate atomic commits (ACID compliant) and non-blocking concurrent reads.
* **Render Cloud PostgreSQL:** Cloud database preserving WhatsApp Web multi-device session credentials and cloud state 24/7.
* **Purged Demo Data:** All synthetic test rows (`Demo Customer`, `Unhappy User`, test bookings) have been completely purged, ensuring a clean production state.

---

## 🛠️ Technology Stack

* **Backend & Cloud Engine:** Python 3.12, FastAPI, Uvicorn, Render Cloud Web Service.
* **WhatsApp Cloud Connectivity:** `neonize>=0.10.0` (pure Python WhatsApp Web multi-device protocol gateway), WebSockets.
* **Database & Persistence:** SQLite (WAL mode with busy timeouts) + Render Managed PostgreSQL (`salon-db`).
* **AI & NLP Frameworks:** `sentence-transformers` (`all-MiniLM-L6-v2`), Scikit-learn, TF-IDF Vectorizer, Regex FSM.
* **Front-End & Operations Portal:** Streamlit Cloud (`salon-ai-0x-ryo.streamlit.app`), Plotly Express / Graph Objects.
* **Testing & Quality Assurance:** `pytest`, `httpx`, Dulwich Git automation.

---

## 🚀 Local Development & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/0x-ryo/Salon-AI.git
cd Salon-AI
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
Verify that all 19 unit, integration, and safety tests pass:
```bash
python -m pytest tests/ -v
```

### 3. Launch Local Streamlit Dashboard
```bash
streamlit run app/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run WhatsApp Cloud Bot Locally (Optional)
```bash
uvicorn app.whatsapp_bot:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to [http://localhost:8000/pair](http://localhost:8000/pair) to view the multi-device link interface.

---

## 📁 Repository Directory Structure

```
Salon-AI/
├── app/
│   ├── app.py                 # Pulse Clinic Front-Desk Reception Portal (Live Counter Operations)
│   ├── pages/
│   │   └── 1_🔬_AI_Evaluation_&_Benchmarks.py # Dedicated Academic Evaluation Lab (INT428)
│   ├── whatsapp_bot.py        # 24/7 Cloud Gateway (Neonize + FastAPI + /pair)
│   ├── salon_config.py        # Enterprise configurations (Razors-n-scissors BH-5)
│   └── config.py              # Application settings & environment loader
├── pages/
│   └── 1_🔬_AI_Evaluation_&_Benchmarks.py     # Root-level multi-page entrypoint for Streamlit Cloud
├── streamlit_app.py           # Root entrypoint redirecting to Pulse Clinic front-desk
├── engine/
│   ├── guardrails.py          # DPDP Act PII Redaction & Medical Safety Filter
│   ├── rule_engine.py         # Approach 1: Regex & FSM Slot-Filling Dialog Tracker
│   ├── semantic_engine.py     # Approach 2: MiniLM Semantic Similarity & Retrieval
│   └── hybrid_agent.py        # Hybrid Orchestrator & XAI Trace Generator
├── database/
│   ├── db.py                  # Relational Schema CRUD, Station Rosters & Interval Capacity Checks
│   └── salon.db               # SQLite Relational Database Cache (WAL Mode)
├── data/
│   ├── knowledge_base.json    # Salon Services, Pricing, & Policies Catalog
│   ├── owner_interview.json   # Authentic Fieldwork Workflow Analysis
│   └── eval_queries.json      # 30+ Benchmark Evaluation Test Suite
├── benchmark/
│   ├── evaluate.py            # Automated Comparison Benchmark Evaluator
│   └── benchmark_results.json # Saved Empirical Metric Results
├── tests/
│   ├── test_whatsapp.py       # Integration tests for WhatsApp bot & endpoints
│   └── test_ai_system.py      # Core agent & safety guardrail tests
├── docs/
│   ├── DEPLOYMENT.md          # 24/7 Cloud deployment & operations guide
│   └── OWNER_EVALUATION_FORM.md # Salon feedback & operational assessment
├── render.yaml                # Render Cloud 24/7 deployment specification
├── requirements.txt           # Python dependencies
└── README.md                  # Comprehensive system documentation
```

---

## 🛡️ Responsible AI, Ethics & Compliance

1. **Digital Personal Data Protection (DPDP Act 2023):** Automatic regex-based redaction of Indian phone numbers (`+91-XXXXXXXXXX`) and names before audit logs are stored.
2. **Medical Diagnosis Boundary Filter:** Explicit refusal of skin or scalp pathology queries, preventing harm and strictly advising consultation with certified medical professionals.
3. **Transparent Non-Discriminatory Pricing:** Rate cards are hardcoded and non-negotiable via the chatbot, guaranteeing zero price surge discrimination.
4. **Explainable AI (XAI):** Each response includes structured execution traces showing intent classification confidence, fired heuristic rules, and retrieved knowledge distances.

---

## 👨‍💻 Student Author & Academic Metadata

* **Name:** Suman Saha
* **Registration No:** 12524973
* **Roll No / Section:** K4P25CB
* **Group:** Group 13
* **Course:** INT428 — Artificial Intelligence Essentials
* **Department:** Department of Computer Science & Engineering
* **Institution:** Lovely Professional University, Punjab, India
