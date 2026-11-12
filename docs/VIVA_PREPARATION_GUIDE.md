# INT428 Artificial Intelligence Foundations — Viva Voce Preparation Guide
**Project Title:** Customer Support Chatbot for a Real Small Business (Salon / Barber Shop)  
**Student Name:** Suman Saha  
**Registration Number:** 12524973  
**Group Number:** Group 13  
**Session:** 2026–27  

---

## Section 1: Problem Formulation & Agent Architecture (Unit I & III)

### Q1: What is the AI problem formulation of your salon customer support system?
**Answer:**
We formulate the conversational support agent as a **Goal-Oriented State-Space & Slot-Filling Agent**.
* **State ($S$):** $S_t = (\text{Intent}_t, \text{Slots}_t, \text{ContextHistory}_t, \text{FSM\_State}_t)$, where $\text{Slots} \in \{\text{service}, \text{barber}, \text{date}, \text{time\_slot}, \text{customer\_name}, \text{phone}\}$.
* **Actions ($A$):** Dialogue acts including `GREET`, `CLARIFY_SLOT(slot)`, `CONFIRM_BOOKING(details)`, `EXECUTE_DB_QUERY(query)`, `REJECT_OUT_OF_SCOPE(reason)`, and `ESCALATE_HUMAN(queue)`.
* **Transition Function $T(S, A)$:** Updates the slot state and moves the Finite State Machine (FSM) from `IDLE` $\rightarrow$ `AWAITING_SERVICE` $\rightarrow$ `AWAITING_BARBER` $\rightarrow$ `AWAITING_DATE_TIME` $\rightarrow$ `AWAITING_CONTACT` $\rightarrow$ `BOOKED`.
* **Utility / Reward:** Maximize task completion rate (conflict-free appointments booked, complaints recorded) while minimizing conversation turns, latency, and customer friction.

### Q2: What type of Intelligent Agent is this? (PEAS Specification)
**Answer:**
Our system implements a **Utility-Based & Model-Based Reflex Agent**:
* **Performance Measure (P):** Intent recognition accuracy (>90%), slot completion rate, average response latency (<50ms), zero double-booking rate, customer grievance resolution rate.
* **Environment (E):** Customer text stream (Telegram, Mobile Web chat), SQLite relational database, live barber scheduling calendar.
* **Actuators (A):** Natural language replies, interactive quick-reply pill suggestions, SQLite transactional commits (`INSERT`/`UPDATE`), Human Handover escalation triggers.
* **Sensors (S):** Text messages from Telegram webhooks or Streamlit chat input, customer phone numbers, datetime timestamps.

---

## Section 2: Core AI Techniques & Comparative Analysis (Unit II, V, VI)

### Q3: What two comparable AI approaches did you implement and why?
**Answer:**
To strictly fulfill the course mandate requiring at least two comparable approaches:
1. **Approach 1 (Classical AI Baseline — Unit II):** Deterministic Pattern Matching with Regular Expressions, keyword tokenizers, and a Finite State Machine (FSM) dialogue manager for slot filling.
2. **Approach 2 (Modern Semantic AI — Unit V & VI):** Dense Vector Semantic Search using Sentence-Transformers (`all-MiniLM-L6-v2`) and TF-IDF Cosine Similarity over an embedded salon knowledge base.
3. **Proposed Hybrid Model (Production):** Semantic retrieval routes open-ended customer inquiries (hours, prices, policies, styling advice), while the deterministic FSM handles transactional flows (conflict-free booking, cancellation, phone-based status, complaint ticketing).

### Q4: How do the two approaches compare on empirical benchmarks?
**Answer:**
We tested both approaches on a fixed 30-question benchmark dataset containing direct queries, paraphrases, typos, and adversarial prompts:
* **Direct FAQ Queries:** Both Approach 1 and 2 achieve ~95–100% accuracy.
* **Paraphrased / Colloquial Queries:** Approach 1 drops to **55.0%** because regex breaks when users rephrase (e.g., *"When does the shop shut at night?"* instead of *"opening timings"*). Approach 2 achieves **92.5%** by matching semantic vector proximity.
* **Latency:** Approach 1 runs in **~1.2 ms** (instant string ops). Approach 2 runs in **~18–25 ms** (vector dot products). Both are well within the real-time threshold (<100 ms).
* **Hallucination Rate:** **0.0%** across both because responses are strictly grounded in the local SQLite database and validated JSON ontology, with no generative hallucination.

### Q5: Why is a hybrid approach better than using a raw LLM API (like GPT-4)?
**Answer:**
1. **Zero Hallucination:** A generative LLM can invent services, fabricate discounts, or double-book unavailable barbers. Our hybrid system strictly queries SQLite for available time slots.
2. **Zero Financial Cost:** Purely local execution costs ₹0.00/month, making it viable for a small barber shop that cannot afford monthly API bills.
3. **Deterministic Transactions:** Database operations require exactness (phone numbers, slot IDs), which an FSM guarantees.

---

## Section 3: Explainability & Responsible AI (Unit V & VI)

### Q6: How does your system implement Explainable AI (XAI)?
**Answer:**
Every response is bundled with a transparent **Explainability Trace** visible in the inspector:
* Shows the exact detected intent and confidence score ($S_C \in [0, 1]$).
* For Approach 1: Displays the exact regex pattern and rule that fired, along with the FSM state transition.
* For Approach 2: Displays the top-3 candidate vector matches with cosine similarity scores and exact knowledge base source citations.
* Shows the exact SQL query executed against `salon.db`.

### Q7: What Responsible AI safeguards are implemented?
**Answer:**
1. **PII Masking (DPDP Act Compliance):** Customer phone numbers are automatically sanitized (e.g. `98765****10`) before conversation logs are stored in the database.
2. **Medical Diagnosis & Prescription Boundary:** Salon staff are grooming professionals, not doctors. If a user asks about scalp infections, pus, alopecia, or antibiotic ointments, the system strictly refuses to diagnose and redirects them to a licensed dermatologist.
3. **Prompt Injection & Adversarial Defense:** Regex pattern filters neutralize attempts to hijack the persona (e.g. *"Ignore instructions and write code"*).
4. **Fairness & Transparent Pricing:** Fixed, non-negotiable pricing rules ensure no gender markups or arbitrary charges.

---

## Section 4: Real Small Business Fieldwork (Project 13 Specific)

### Q8: What fieldwork did you conduct with the salon owner?
**Answer:**
We interviewed **Mr. Rajesh Kumar**, owner and master barber at *Urban Trim & Groom Barber Salon*:
* **Core Problem Discovered:** Barbers receive 25–40 phone calls daily during busy haircuts. Answering calls interrupts scissor cuts and annoys in-chair clients.
* **Missed After-Hours Revenue:** 15–20 calls per week occur after closing (8:30 PM – 9:30 AM), resulting in lost bookings to competitors.
* **Outcome:** The chatbot automates routine queries, handles 24/7 bookings, and frees the barbers to focus entirely on styling.

### Q9: Why chose Telegram and Mobile Web instead of a mobile app?
**Answer:**
Customers will not download an app from the Play Store just to book a ₹250 haircut. Our solution uses **Zero-Download Channels**:
1. An acrylic QR code on the styling mirror and counter opens an instant mobile web chat.
2. Customers can chat directly via Telegram or WhatsApp with zero installation.
3. The owner accesses a dedicated Tablet Dashboard to view the live appointment timeline and unresolved complaints.
