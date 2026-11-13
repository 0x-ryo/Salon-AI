"""
Razors-n-scissors — Real WhatsApp Number Automation Bot (+91 6284421638)
INT428 Course Project (Group 13 - Suman Saha | Reg: 12524973)

Runs WhatsApp Web automation using Selenium:
- Pairs directly with phone number +91 6284421638 via WhatsApp 8-digit Pairing Code
- Zero Facebook account needed, zero Twilio cost
- Listens for inbound customer messages
- Passes them to HybridSalonAgent (Interactive Menu, Slot-filling, Semantic Retrieval)
- Types and sends responses directly inside WhatsApp Web in real-time
- Saves session state permanently in ./whatsapp_session directory
"""

import os
import sys
import time
import re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.hybrid_agent import HybridSalonAgent
from engine.rule_engine import get_master_menu
from database.db import init_db

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Selenium or webdriver-manager not found. Please install via pip.")
    sys.exit(1)

TARGET_PHONE = "916284421638"
SESSION_DIR = os.path.join(PROJECT_ROOT, "whatsapp_session")

def get_driver():
    """Configures Chrome with persistent profile for WhatsApp Web."""
    os.makedirs(SESSION_DIR, exist_ok=True)
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={SESSION_DIR}")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Standard User-Agent to avoid detection
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Fallback to system chrome
        driver = webdriver.Chrome(options=chrome_options)

    return driver


def is_logged_in(driver):
    """Checks if WhatsApp Web main chat interface has loaded."""
    try:
        # Look for the chat list / search bar or profile icon
        driver.find_element(By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]')
        return True
    except Exception:
        try:
            driver.find_element(By.XPATH, '//div[@id="side"]')
            return True
        except Exception:
            return False


def request_pairing_code(driver, phone_number):
    """Clicks 'Link with phone number' on WhatsApp Web and retrieves the 8-digit code."""
    print(f"\n[WhatsApp Pairing] Navigating to WhatsApp Web for {phone_number}...")
    driver.get("https://web.whatsapp.com")

    # Wait for pairing page to load
    time.sleep(5)

    try:
        # Click "Link with phone number" link
        link_phone_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//span[@role="button" and (contains(text(), "phone number") or contains(text(), "Link with"))]'))
        )
        link_phone_btn.click()
        print("[WhatsApp Pairing] Clicked 'Link with phone number' button.")
        time.sleep(2)

        # Enter phone number
        phone_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="text"]'))
        )
        phone_input.click()
        phone_input.clear()
        
        # Enter clean 10-digit number
        clean_num = phone_number[-10:]
        phone_input.send_keys(clean_num)
        print(f"[WhatsApp Pairing] Entered phone: {clean_num}")
        time.sleep(1)

        # Click Next button
        next_btn = driver.find_element(By.XPATH, '//div[@role="button" and (contains(., "Next") or contains(., "CONTINUE"))]')
        next_btn.click()
        print("[WhatsApp Pairing] Generating 8-digit pairing code...")
        time.sleep(4)

        # Retrieve the 8-character pairing code
        code_elements = driver.find_elements(By.XPATH, '//span[@data-lexical-text="true" or contains(@class, "pairing-code")]')
        code = "".join([el.text for el in code_elements if el.text.isalnum()])
        
        if not code or len(code) < 4:
            # Fallback xpath for code containers
            code_containers = driver.find_elements(By.XPATH, '//div[contains(@class, "landing-wrapper")]//span')
            code = "".join([c.text.strip() for c in code_containers if len(c.text.strip()) == 1 and c.text.strip().isalnum()])

        if code:
            # Format as XXXX-YYYY
            formatted = f"{code[:4]}-{code[4:]}" if len(code) == 8 else code
            print("\n" + "=" * 65)
            print(f"📱 WHATSAPP PAIRING CODE FOR +{phone_number}:")
            print(f"👉   >>>  {formatted}  <<<")
            print("=" * 65)
            print("Steps on your phone:")
            print("1. Open WhatsApp on +91 6284421638")
            print("2. Tap ⋮ (Three dots) > Linked Devices > Link a Device")
            print("3. Tap 'Link with phone number instead'")
            print(f"4. Enter code: {formatted}")
            print("=" * 65 + "\n")
            return formatted
    except Exception as e:
        print(f"[WhatsApp Pairing Note]: {e}")

    return None


def run_whatsapp_listener():
    """Main loop: listens for incoming messages and replies via HybridSalonAgent."""
    init_db()
    driver = get_driver()
    driver.get("https://web.whatsapp.com")
    print("\n[WhatsApp Bot] Opened WhatsApp Web. Checking session status...")

    # Wait for login or request pairing
    paired = False
    for _ in range(6):
        if is_logged_in(driver):
            paired = True
            break
        time.sleep(3)

    if not paired:
        request_pairing_code(driver, TARGET_PHONE)
        print("[WhatsApp Bot] Waiting for user to confirm pairing on phone...")
        while not is_logged_in(driver):
            time.sleep(3)

    print("\n" + "=" * 60)
    print(f"🎉 WHATSAPP BOT IS LIVE ON +91 6284421638!")
    print("Listening for incoming messages in real-time...")
    print("=" * 60 + "\n")

    user_sessions = {}

    while True:
        try:
            # Look for unread message badges in chat list
            unread_chats = driver.find_elements(By.XPATH, '//span[contains(@aria-label, "unread") or contains(@aria-label, "Unread")]')
            
            for unread in unread_chats:
                try:
                    # Click into the unread chat
                    unread.click()
                    time.sleep(1.5)

                    # Extract sender / contact header
                    try:
                        header = driver.find_element(By.XPATH, '//header//span[@dir="auto"]')
                        sender_name = header.text.strip()
                    except Exception:
                        sender_name = "Customer"

                    # Extract the latest received message text
                    incoming_bubbles = driver.find_elements(By.XPATH, '//div[contains(@class, "message-in")]//span[contains(@class, "selectable-text")]')
                    if not incoming_bubbles:
                        continue
                    
                    last_msg_el = incoming_bubbles[-1]
                    incoming_text = last_msg_el.text.strip()

                    if not incoming_text:
                        continue

                    print(f"\n[WhatsApp Inbound] From '{sender_name}': {incoming_text}")

                    # Get or create hybrid agent session for this sender
                    if sender_name not in user_sessions:
                        user_sessions[sender_name] = HybridSalonAgent()
                        agent = user_sessions[sender_name]
                        # Set default customer name if clean
                        if sender_name != "Customer" and not sender_name.startswith("+"):
                            agent.rule_engine.slots["customer_name"] = sender_name

                    agent = user_sessions[sender_name]

                    # Process message through AI Agent
                    result = agent.handle_message(incoming_text, engine_mode="Hybrid")
                    reply_text = result.get("response", get_master_menu())

                    # Cloud sync to Render so Streamlit Cloud dashboard updates immediately
                    if "Appointment #" in reply_text and "confirmed" in reply_text.lower():
                        try:
                            import requests
                            slots = agent.rule_engine.slots
                            requests.post(
                                "https://salon-ai-backend-6xdf.onrender.com/api/action/book",
                                json={
                                    "customer_name": slots.get("customer_name") or sender_name,
                                    "phone": TARGET_PHONE,
                                    "service_id": slots.get("service") or 1,
                                    "barber_id": slots.get("barber") or 1,
                                    "date_str": str(slots.get("date") or "2026-11-14"),
                                    "time_str": str(slots.get("time") or "10:00")
                                },
                                timeout=3.0
                            )
                            print("[Cloud Sync] ✅ Successfully synced new booking to live Streamlit Cloud dashboard!")
                        except Exception as sync_e:
                            print(f"[Cloud Sync Note]: {sync_e}")

                    print(f"[WhatsApp Reply]: {reply_text[:60]}...")

                    # Type and send reply in message input box
                    input_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @data-tab="10"]'))
                    )
                    input_box.click()

                    # Send line by line to preserve newlines
                    for line in reply_text.split("\n"):
                        input_box.send_keys(line)
                        input_box.send_keys(Keys.SHIFT, Keys.ENTER)
                    
                    # Press Enter to send
                    input_box.send_keys(Keys.ENTER)
                    time.sleep(1)
                    print("✅ Reply delivered successfully!")

                except Exception as chat_err:
                    print(f"[Chat Handling Note]: {chat_err}")
                    continue

            time.sleep(2)

        except KeyboardInterrupt:
            print("\nShutting down WhatsApp Bot...")
            break
        except Exception as loop_err:
            time.sleep(3)
            continue

    driver.quit()

if __name__ == "__main__":
    run_whatsapp_listener()
