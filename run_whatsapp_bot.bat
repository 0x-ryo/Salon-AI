@echo off
title Razors-n-scissors WhatsApp Bot (Twilio)
echo ============================================================
echo   Razors-n-scissors - WhatsApp Bot (Twilio Webhook)
echo ============================================================
echo.
echo Make sure you have set the following environment variables:
echo   TWILIO_ACCOUNT_SID
echo   TWILIO_AUTH_TOKEN
echo   TWILIO_WHATSAPP_FROM   (e.g. whatsapp:+14155238886)
echo.
echo Starting FastAPI server on http://0.0.0.0:8000
echo Twilio Webhook URL (set in console): http://YOUR_PUBLIC_URL/whatsapp/webhook
echo.
"C:\Users\suman\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app.whatsapp_bot:app --host 0.0.0.0 --port 8000 --reload
pause
