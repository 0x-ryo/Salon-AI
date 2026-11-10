# CSE276 Course Project Presentation: Urban Trim & Groom Barber Salon AI
**Course:** CSE276 Artificial Intelligence Foundations  
**Topic:** Customer Support Chatbot for a Real Small Business (Project 13)  
**Presenter:** Suman Saha (Reg: 12524973, Group 13)  
**Institution:** Lovely Professional University  

---

## Slide 1: Title & Project Scope
* **Project Title:** Customer Support & Operations Chatbot for Urban Trim & Groom Barber Salon
* **Course:** CSE276 · Artificial Intelligence Foundations (CA Project)
* **Student:** Suman Saha (Solo Execution, Group 13)
* **Real-World Small Business:** Urban Trim & Groom Barber Salon (Model Town, Jalandhar)
* **Key Innovation:** Zero customer app download (Mobile Web / QR & Telegram) + Dual AI Engine (Classical Rule-Based FSM vs Dense Vector Retrieval).

---

## Slide 2: Fieldwork & Business Problem Statement
* **Fieldwork Interview:** Conducted structured interview with Mr. Rajesh Kumar (Owner, 14 yrs experience).
* **Pain Point 1:** Stylists interrupted 25–40 times daily by phone calls during delicate haircutting.
* **Pain Point 2:** 30% of calls occur after hours (8:30 PM to 9:00 AM) resulting in lost clients to competitors.
* **Pain Point 3:** Double bookings and lost grievances (dissatisfied clients leaving 1-star Google reviews instead of resolving in-house).
* **Solution:** 24/7 automated conversational booking, service FAQ matching, complaint desk, and human handover queue.

---

## Slide 3: AI Problem Formulation (State Space & Agent Model)
* **Agent Architecture:** Goal-Oriented State-Space & Slot-Filling Reflex Agent with Fallback Boundaries.
* **State Space Formulation:**
  $$S_t = \langle \mathcal{I}_t, \mathcal{S}_t, \mathcal{H}_t, \mathcal{F}_t \rangle$$
  * $\mathcal{I}_t$: Detected Intent (16 salon intent classes)
  * $\mathcal{S}_t$: Slots $\{\text{service}, \text{barber}, \text{date}, \text{time}, \text{name}, \text{phone}\}$
  * $\mathcal{F}_t$: Finite State Machine state (`IDLE`, `AWAITING_SERVICE`, `AWAITING_BARBER`, `AWAITING_TIME`, `CONFIRMED`)
* **PEAS Specification:**
  * **P:** Intent accuracy, latency (<20ms), slot completion rate, 0% double-booking.
  * **E:** Telegram/Web chat stream, SQLite database, dynamic barber schedule.
  * **A:** Natural language responses, SQLite transactional commits, human handover flags.
  * **S:** Customer text tokens, phone numbers, timestamps.

---

## Slide 4: Dual AI Implementation (CSE276 Core Requirement)
* **Approach 1 (Classical AI — Unit II):**
  * Deterministic Pattern-Matching (Regex + Lexical Tokenizer).
  * Finite State Machine (FSM) slot-filling dialog manager.
  * Full step-by-step rule firing trace.
* **Approach 2 (Modern Semantic AI — Unit V & VI):**
  * Dense Vector Retrieval using Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dimensional).
  * TF-IDF Cosine Similarity baseline.
  * Semantic confidence thresholding ($\tau = 0.35$).
* **Proposed Hybrid Model (Production):**
  * Semantic vector matching handles diverse natural language inquiries and FAQs.
  * Deterministic FSM executes transactional booking, cancellation, and complaint commits.

---

## Slide 5: Empirical Benchmark & Comparative Evaluation
* Evaluated against **30 fixed benchmark queries** across 7 distinct categories:

| Metric | Approach 1 (Rule-Based FSM) | Approach 2 (Semantic Retrieval) | Proposed Hybrid Model |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | 50.0% | 80.0% | **100.0%** |
| **Paraphrase Handling** | 60.0% | **100.0%** | **100.0%** |
| **Average Latency** | **3.04 ms** | 14.13 ms | 13.29 ms |
| **Safety Refusal Rate** | 40.0% | 60.0% | **100.0%** |
| **Hallucination Rate** | **0.0%** | **0.0%** | **0.0%** |

* **Insight:** Rule-based bots fail on colloquial rephrasings; semantic search understands intent variation; hybrid architecture delivers 100% accuracy and safety.

---

## Slide 6: Explainable AI (XAI) & Responsible AI
* **XAI Live Traces:** Every response includes an inspectable reasoning trace showing detected intent, confidence score, fired rules, matched vector candidates, and SQL queries.
* **PII Redaction (DPDP Act):** Automatic regex sanitization of phone numbers and emails (`98765****10`) before database audit logging.
* **Medical Scope Refusal:** Active detection and refusal of scalp infection / antibiotic requests, redirecting users to medical dermatologists.
* **Prompt Injection Defense:** Neutralizes system override attacks and directive jailbreaks.

---

## Slide 7: Working Interface & Deployment
* **Channel 1 (Mobile Web / QR Code):** Zero-friction chat interface with interactive pill buttons.
* **Channel 2 (Telegram Bot):** Live conversational bot running via `python-telegram-bot` (`@UrbanTrimSalonBot`).
* **Channel 3 (Salon Tablet Portal):** Real-time booking calendar, projected revenue, unresolved complaint tickets, and urgent human handover notifications.

---

## Slide 8: Business Impact & Conclusion
* **Owner Rating:** **4.9 / 5.0** overall usefulness score from Mr. Rajesh Kumar.
* **Economics:** Saves ₹12,000–₹18,000/month in receptionist costs; captures ₹6,000–₹9,000 in missed after-hours bookings.
* **Academic Takeaway:** Fully satisfies CSE276 syllabus across classical search, intelligent agents, semantic representation, comparative evaluation, and Responsible AI.
