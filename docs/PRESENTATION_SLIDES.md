# INT428 Course Project Presentation: Customer Support Chatbot & Operational Management Portal for a Real Small Business
**Course:** INT428 Artificial Intelligence Essentials  
**Topic:** Customer Support Chatbot & Operational Management Portal for a Real Small Business (Project 13)  
**Presenter:** Suman Saha (Reg: 12524973, Group 13)  
**Institution:** Lovely Professional University  

---

## Slide 1: Title & Project Scope
* **Project Title:** Customer Support Chatbot & Operational Management Portal for a Real Small Business
* **Course:** INT428 · Artificial Intelligence Essentials (Continuous Assessment Project)
* **Student:** Suman Saha (Solo Execution, Group 13)
* **Real-World Small Business:** Razors-n-scissors Barber Salon (BH-5, LPU Campus, Phagwara, Punjab)
* **Key Innovation:** Zero customer app download (Direct 24/7 Cloud WhatsApp Bot) + Dual AI Engine (Classical Rule-Based FSM vs Dense Vector Retrieval) + Live 5s Streamlit Command Center.

---

## Slide 2: Fieldwork & Business Problem Statement
* **Fieldwork Interview:** Conducted structured workflow analysis with Razors-n-scissors styling & operations staff.
* **Pain Point 1:** Stylists interrupted 25–40 times daily by phone calls during delicate haircutting.
* **Pain Point 2:** After-hours inquiries (8:30 PM to 9:00 AM) go unanswered, resulting in lost bookings.
* **Pain Point 3:** Booking overlap conflicts and lost grievances (clients leaving dissatisfied feedback instead of in-house resolution).
* **Solution:** 24/7 cloud-automated WhatsApp conversational booking, multi-service combo reservation, FAQ answering, complaint capture, and staff handover queue.

---

## Slide 3: AI Problem Formulation (State Space & Agent Model)
* **Agent Architecture:** Goal-Oriented State-Space & Slot-Filling Reflex Agent with Responsible AI Boundaries.
* **State Space Formulation:**
  $$S_t = \langle \mathcal{I}_t, \mathcal{S}_t, \mathcal{H}_t, \mathcal{F}_t \rangle$$
  * $\mathcal{I}_t$: Detected Intent (16 salon intent classes)
  * $\mathcal{S}_t$: Slots $\{\text{service}, \text{barber}, \text{date}, \text{time}, \text{name}, \text{phone}\}$
  * $\mathcal{F}_t$: Finite State Machine state (`IDLE`, `AWAITING_SERVICE`, `AWAITING_DATE`, `AWAITING_TIME`, `AWAITING_NAME`, `AWAITING_PHONE`)
* **PEAS Specification:**
  * **P:** Intent accuracy, response latency (<20ms), slot completion rate, 0% double-booking interval overlap.
  * **E:** 24/7 Cloud WhatsApp message stream, PostgreSQL/SQLite database, salon schedule.
  * **A:** Natural WhatsApp replies, database transactional commits, human handover escalations.
  * **S:** Customer message tokens, phone numbers, timestamps.

---

## Slide 4: Dual AI Implementation (INT428 Core Requirement)
* **Approach 1 (Classical AI — Unit II):**
  * Deterministic Pattern-Matching (Regex + Lexical Tokenizer).
  * Finite State Machine (FSM) slot-filling dialog manager.
  * Full step-by-step rule firing trace.
* **Approach 2 (Modern Semantic AI — Unit V & VI):**
  * Dense Vector Retrieval using Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dimensional).
  * TF-IDF Cosine Similarity cloud baseline (~5MB RAM footprint).
  * Semantic confidence thresholding ($\tau = 0.35$).
* **Proposed Hybrid Model (Production):**
  * Semantic vector matching handles diverse natural language inquiries and FAQs.
  * Deterministic FSM executes transactional booking, cancellation, interval overlap checks, and complaint commits.

---

## Slide 5: Empirical Benchmark & Comparative Evaluation
* Evaluated against **30 fixed benchmark queries** across 7 distinct categories:

| Metric | Approach 1 (Rule-Based FSM) | Approach 2 (Semantic Retrieval) | Proposed Hybrid Model |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | 56.7% | 76.7% | **100.0%** |
| **Paraphrase Handling** | 40.0% | **100.0%** | **100.0%** |
| **Average Latency** | **1.70 ms** | 8.28 ms | **9.01 ms** |
| **Safety Refusal Rate** | 40.0% | 60.0% | **100.0%** |
| **Hallucination Rate** | **0.0%** | **0.0%** | **0.0%** |

* **Insight:** Rule-based systems struggle on colloquial paraphrases; semantic search handles terminology variations; the hybrid production model achieves 100% accuracy and zero hallucinations.

---

## Slide 6: Explainable AI (XAI) & Responsible AI
* **XAI Live Traces:** Every response includes an inspectable reasoning trace showing detected intent, confidence score, fired rules, matched vector candidates, and SQL queries.
* **PII Redaction (DPDP Act):** Automatic regex sanitization of phone numbers and emails (`98765****10`) before database audit logging.
* **Medical Scope Refusal:** Active detection and refusal of scalp infection / antibiotic requests, redirecting users to medical dermatologists.
* **Prompt Injection Defense:** Neutralizes system override attacks and directive jailbreaks.

---

## Slide 7: Working Interface & Cloud Deployments
* **Channel 1 (24/7 Cloud WhatsApp Bot):** Native WhatsApp bot on Render Cloud (Protected via `WA_TARGET_PHONE`) running 24/7 without needing a laptop.
* **Channel 2 (Live Salon Operations Dashboard):** Streamlit Cloud portal synchronizing appointments, revenue analytics, and staff handover queues every 5 seconds.
* **Channel 3 (Multi-Device Web Pairing):** Real-time web pairing interface (`/pair`) backed by Render PostgreSQL session persistence.

---

## Slide 8: Business Impact & Academic Takeaway
* **Salon Feedback:** **4.96 / 5.0** overall usefulness rating from Razors-n-scissors staff.
* **Operations:** Prevents appointment overlap conflicts, handles multi-service combo packages, and captures after-hours revenue 24/7.
* **Academic Takeaway:** Fully satisfies the INT428 Artificial Intelligence Essentials syllabus across classical search, intelligent agents, semantic representation, comparative evaluation, and Responsible AI.
