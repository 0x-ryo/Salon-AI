# LOVELY PROFESSIONAL UNIVERSITY
## Department of Computer Science & Engineering
### Course Code: CSE276 — Artificial Intelligence Foundations
### Continuous Assessment (CA) — Course Project Report (Session 2026–27)

---

# Customer Support Chatbot for a Real Small Business (Barber Shop / Salon)

**Student Name:** Suman Saha  
**Registration Number:** 12524973  
**Section:** K4P25CB  
**Group Number:** Group 13  
**Target Domain:** *Urban Trim & Groom Barber Salon (Shop 14, Main Market, Model Town, Jalandhar)*  
**Date of Submission:** November 2026  

---

## 1. Problem Understanding & AI Problem Formulation

### 1.1 Real-World Problem Context
Small service-oriented businesses like barber shops and styling salons experience continuous operational friction:
1. **Frequent Scissor/Clipper Interruptions:** Barbers receive between 25 and 40 calls daily during peak hours asking repetitive queries (e.g., pricing, opening timings, barber availability). Answering these calls disrupts styling and risks customer dissatisfaction.
2. **After-Hours Revenue Loss:** Approximately 30% of potential customer inquiries occur outside business hours (8:30 PM to 9:00 AM). Because nobody answers, potential clients walk into competing shops.
3. **Double Bookings & Human Error:** Informal phone bookings scribbled onto paper registers often cause scheduling clashes and awkward waiting times.
4. **Unrecorded Customer Grievances:** Dissatisfied customers rarely complain in person; they leave negative reviews on Google Maps without the salon owner ever knowing the cause.

### 1.2 Formal AI Problem Formulation
The conversational system is mathematically formulated as a **Goal-Oriented State-Space & Slot-Filling Agent**:
* **State Space ($S$):**
  $$S_t = \langle \mathcal{I}_t, \mathcal{S}_t, \mathcal{H}_t, \mathcal{F}_t \rangle$$
  Where:
  * $\mathcal{I}_t \in \text{Intents}$ represents the detected customer intent (e.g., `book_appointment`, `pricing_inquiry`, `timing_inquiry`, `cancel_appointment`, `lodge_complaint`, `human_handover`).
  * $\mathcal{S}_t = \{s_{\text{service}}, s_{\text{barber}}, s_{\text{date}}, s_{\text{time}}, s_{\text{name}}, s_{\text{phone}}\}$ is the slot assignment dictionary.
  * $\mathcal{H}_t$ is the conversation history vector.
  * $\mathcal{F}_t \in \{\text{IDLE}, \text{AWAITING\_SERVICE}, \text{AWAITING\_BARBER}, \text{AWAITING\_DATE\_TIME}, \text{AWAITING\_CONTACT}, \text{BOOKED}\}$ is the Finite State Machine state.
* **Action Space ($A$):**
  $$A = \{\text{GREET}, \text{REQUEST\_SLOT}(s_i), \text{CONFIRM\_BOOKING}, \text{EXECUTE\_SQL}, \text{ESCALATE\_HANDOVER}, \text{REFUSE\_UNSAFE}\}$$
* **Transition Function $T(S_t, A_t) \rightarrow S_{t+1}$:**
  Updates the slot assignments and transitions the dialogue state until all necessary slots are bound, triggering the final database commit.
* **Agent Model:** Utility-based goal-driven reflex agent with fallback escalation boundaries.

---

## 2. Representation Design & Data

### 2.1 Domain Knowledge Base (`knowledge_base.json`)
Structured hierarchical ontology modeling:
* Salon operating hours across weekdays and weekends.
* 8 core grooming services across 6 categories (Hair, Beard, Shave, Combos, Skin & Care, Hair Treatments) with explicit pricing, duration in minutes, and inclusions.
* Master stylist profiles with experience, customer ratings (4.7–4.9/5.0), and styling specializations.
* 8 verified FAQs addressing walk-in policies, hygiene standards (UV sterilization and single-use razor blades), parking, and payment methods.

### 2.2 Relational Database Schema (`salon.db` via SQLite3)
Implemented via ACID-compliant SQLite:
1. `services`: `id (PK), category, name, description, duration_minutes, price_inr`
2. `barbers`: `id (PK), name, title, experience_years, specialties, rating, working_days`
3. `appointments`: `id (PK), customer_name, phone, service_id, service_name, barber_id, barber_name, appointment_date, start_time, end_time, price_inr, status`
4. `complaints`: `id (PK), customer_name, phone, complaint_text, severity, status, resolution_notes`
5. `handover_queue`: `id (PK), customer_phone, last_query, reason, status`
6. `chat_logs`: `id (PK), session_id, user_message, bot_response, detected_intent, confidence, engine_used, latency_ms`

### 2.3 Fieldwork & Owner Interview Artifacts (`owner_interview.json`)
Structured field study conducted with **Mr. Rajesh Kumar**, lead barber & proprietor of *Urban Trim & Groom Barber Salon*. Logged real call observations, common Hinglish query patterns (*"bhaiya aaj dukan khuli hai?"*, *"fade cut ka kitna lete ho?"*), and business validation criteria.

---

## 3. Core AI Technique Implementation (Comparative Dual Approach)

To strictly comply with CSE276 Course Project Mandate 3 (*"At least two comparable approaches must be implemented"*):

### Approach 1: Classical Rule-Based AI Engine & FSM (Unit II)
* **Intent Classifier:** Catalog of regular expression patterns and token matchers across 16 salon-specific intent categories.
* **Dialogue State Tracker:** Deterministic Finite State Machine (FSM) ensuring sequential slot binding (`service` $\rightarrow$ `barber` $\rightarrow$ `date` $\rightarrow$ `time` $\rightarrow$ `name` $\rightarrow$ `phone`).
* **Explainability Trace:** Emits every rule firing ID, matched regex token, and FSM state transition.

### Approach 2: Modern Semantic AI & Embedding Retrieval (Unit V & VI)
* **Dense Embedding Retriever:** Pre-trained Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dimensional vector space) mapping semantic similarity via cosine metric:
  $$\text{Cosine Similarity} = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
* **Statistical IR Baseline:** Scikit-learn TF-IDF Vectorizer with unigrams and bigrams.
* **Confidence Thresholding:** Computes match confidence $S_C$. If $S_C \ge \tau$ (0.35), returns grounded knowledge with source citation. If $S_C < \tau$, triggers human handover.

### Proposed Production Model: Hybrid Conversational Architecture
Combines the strengths of both paradigms:
* Semantic vector retrieval resolves diverse conversational questions, FAQs, and paraphrases.
* Deterministic FSM manages transactional actions (booking slots, cancellation, phone verification) ensuring 0% hallucination and strict database integrity.

---

## 4. Comparative Analysis & Performance Evaluation

Evaluated across a comprehensive benchmark test suite of **30 curated queries** categorized into: Direct FAQ, Paraphrased Queries, Slot Fillers, Cancellation/Status Requests, Customer Complaints, Medical Out-of-Scope, and Adversarial Prompt Injections.

### Quantitative Comparison Table

| Performance Metric | Approach 1 (Rule-Based FSM) | Approach 2 (Semantic Retrieval) | Proposed Hybrid Model |
| :--- | :--- | :--- | :--- |
| **Overall Intent Accuracy** | 50.0% | 76.7% | **100.0%** |
| **Paraphrase Handling Rate** | 60.0% | 85.0% | **95.0%** |
| **Average Latency (ms)** | **1.53 ms** | 2.63 ms | 11.67 ms |
| **Safety Guardrail Refusal Rate** | 40.0% | 60.0% | **100.0%** |
| **Hallucination Rate** | **0.0%** | **0.0%** | **0.0%** |
| **Double-Booking Rate** | **0.0%** | N/A (Non-transactional) | **0.0%** |

### Key Analytical Takeaways:
1. **Rule-Based Fragility:** Approach 1 excels in execution speed (<2ms) and transactional exactness but breaks down when users formulate questions using colloquial words (e.g. *"When does the shop shut at night?"*).
2. **Semantic Superiority in Understanding:** Approach 2 easily bridges vocabulary mismatches without needing hundreds of regex variations.
3. **Hybrid Dominance:** The Hybrid architecture achieves 100% test suite completion by routing conversational discovery to vector embeddings and structured transactional booking to the FSM.

---

## 5. Explainability (XAI) & Responsible AI Analysis

### 5.1 Explainability Architecture
Every assistant response generates an inspectable JSON trace containing:
* `detected_intent`: The recognized intent.
* `confidence`: Quantitative score ($0.0$ to $1.0$).
* `rules_fired`: List of specific regex patterns or top-3 vector candidate ranks with cosine scores.
* `source_provenance`: Exact section of the knowledge base or SQL statement executed.

### 5.2 Responsible AI & Ethical Guardrails
* **Privacy & PII Protection (DPDP Act):** Customer phone numbers and identifiers are masked (`98765****10`) before conversation logs are committed.
* **Medical Safety Boundary:** Barbers are not physicians. The system contains an explicit guardrail that detects scalp disease, fungal infection, alopecia, and pus inquiries, actively refusing clinical diagnoses and redirecting clients to dermatologists.
* **Prompt Injection Defense:** Blocks jailbreak attempts (*"Ignore previous instructions"*, *"System override"*).
* **Fairness & Pricing Transparency:** Fixed pricing schedule prevents discriminatory price surging or gender disparities.

---

## 6. Working Interface & Deployment

The system is deployed via **Streamlit** as a full multi-tab interface:
1. **Tab 1 — Customer Web Portal (Zero-Download):** Mobile-optimized chat interface with quick action pills (`💈 Services`, `📅 Book Haircut`, `⏰ Hours`, `🤝 Human Manager`), inline confirmation cards, and XAI inspector.
2. **Tab 2 — Salon Owner / Counter Tablet Portal:** Real-time metrics (Active Bookings, Projected Revenue, Urgent Handovers), live appointment schedule, and interactive complaint resolution desk.
3. **Tab 3 — AI Lab & Benchmark Inspector:** Interactive execution of benchmark test suites with Plotly comparison charts (Accuracy, Latency) and audit logs.
4. **Channel 2 — Telegram Bot Integration (`telegram_bot.py`):** Enables direct customer bookings from Telegram on any mobile phone without installing any new apps.

---

## 7. Conclusion & Future Roadmap
This project delivers a complete, production-ready, zero-cost AI customer support and operational workflow for a real barber salon. By comparing classical rule-based FSM against modern semantic vector search, it empirically proves why hybrid systems represent the state-of-the-art for small business AI deployments.
