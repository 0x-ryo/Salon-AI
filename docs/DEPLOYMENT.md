# Deployment & Operations Guide — Customer Support Salon-AI & Operational Management Portal for a Real Small Business
### Razors-n-scissors Barber Salon (BH-5, LPU Campus)
**Course:** INT428 Artificial Intelligence Essentials · Group 13 · Suman Saha (Reg: 12524973)

---

## 🌐 Live Cloud Infrastructure

| Component | Host Platform | Access URL | Description |
| :--- | :--- | :--- | :--- |
| **Live Operations Dashboard** | Streamlit Community Cloud | [salon-ai-0x-ryo.streamlit.app](https://salon-ai-0x-ryo.streamlit.app/) | Counter operations portal, booking calendar, revenue analytics, and INT428 AI Lab Inspector. |
| **24/7 Cloud Bot Gateway** | Render Web Service | [salon-ai-backend-6xdf.onrender.com](https://salon-ai-backend-6xdf.onrender.com) | Python FastAPI engine running 24/7 without requiring a laptop to remain on. |
| **Device Pairing Interface** | Render Cloud Web App | [`/pair` Pairing Screen](https://salon-ai-backend-6xdf.onrender.com/pair) | Real-time multi-device pairing interface with automatic reconnect and QR tab. |
| **Persistent Storage** | Render PostgreSQL (`salon-db`) | Cloud Relational Database | Secure cloud database preserving multi-device session credentials across server restarts. |
| **Target Salon WhatsApp** | Official Salon Number | **`+91 XXXXX-XXXXX`** *(Configured via `WA_TARGET_PHONE`)* | Real WhatsApp Business channel for customer bookings, rate inquiries, and grievances. |

---

## 💻 Local Development & Testing

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/0x-ryo/Salon-AI.git
cd Salon-AI

# Install production dependencies
pip install -r requirements.txt
```

### 2. Launch Streamlit Operations Dashboard Locally
```bash
streamlit run app/app.py
```
Opens in your browser at `http://localhost:8501`.

### 3. Run Automated Pytest Test Suite
```bash
python -m pytest tests/ -v
```
Executes all 19 integration tests covering PII redaction, safety guardrails, interval overlap prevention, multi-turn dialog, and hybrid explainability traces.

### 4. Run Empirical Comparative Benchmark
```bash
python -m benchmark.evaluate
```
Evaluates Approach 1 (Rule-Based FSM) vs. Approach 2 (Semantic Retrieval) vs. the Hybrid Production Agent against 30 benchmark queries.

---

## ☁️ Cloud Deployment Configuration

### Render Cloud Web Service (`render.yaml`)
* **Environment:** Python 3.12 (Native Docker Container)
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `python -m app.whatsapp_bot`
* **Health Check Path:** `/health`
* **Environment Variables:**
  * `PORT=8000`
  * `DATABASE_URL`: Connection string to Render PostgreSQL (`salon-db`)
  * `WA_TARGET_PHONE`: Target salon WhatsApp phone number (configured securely in Render dashboard)

---

## 📞 Support & Salon Contact
* **Salon:** Razors-n-scissors Barber Salon (BH-5, LPU Campus, Phagwara, Punjab)
* **WhatsApp Channel:** Protected (Configured dynamically via `WA_TARGET_PHONE` secret)
* **Student Developer:** Suman Saha (12524973, Group 13)
