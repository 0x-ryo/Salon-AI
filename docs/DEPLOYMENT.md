# Deployment Guide — Razors-n-scissors AI Chatbot
**INT428 | Group 13 | Suman Saha**

---

## Prerequisites
```bash
pip install -r requirements.txt
# New packages added: fastapi uvicorn twilio
```

---

## 1. Owner Dashboard (Streamlit)
```bash
streamlit run app/app.py
```
Opens at http://localhost:8501 — for the salon owner only.

---

## 2. Telegram Bot (Channel 1)
1. Create a bot via [@BotFather](https://t.me/botfather) → `/newbot`
2. Copy the token and run:
```bash
python -m app.telegram_bot <TELEGRAM_BOT_TOKEN>
```

---

## 3. WhatsApp Bot via Twilio (Channel 2)

### 3a. Twilio Sandbox Setup (Free)
1. Sign up at https://www.twilio.com (free)
2. Go to **Messaging → Try it out → Send a WhatsApp message**
3. Note your **Sandbox Number** (e.g. `+1 415 523 8886`)
4. Have customers join the sandbox by sending the join code to that number

### 3b. Environment Variables
Set these before running the webhook:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### 3c. Run the Webhook Server
```bash
uvicorn app.whatsapp_bot:app --host 0.0.0.0 --port 8000
```

### 3d. Expose Publicly with ngrok (for testing)
```bash
ngrok http 8000
# Copy the https URL e.g. https://abc123.ngrok.io
```
Set webhook URL in Twilio Console:
```
https://abc123.ngrok.io/whatsapp/webhook
```

### 3e. Always-On Free Hosting (Railway)
1. Push your code to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Set the start command: `uvicorn app.whatsapp_bot:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in Railway dashboard
5. Copy the Railway public URL and set it as the Twilio webhook

---

## 4. Run Tests
```bash
python -m pytest tests/ -v
```

---

## 5. Run Benchmark
```bash
python -m benchmark.evaluate
```

---

## Contact
Salon WhatsApp: **+91 9877175449**
