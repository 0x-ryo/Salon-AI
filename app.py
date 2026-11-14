import os
import sys

# Define package path so 'from app.whatsapp_bot' works seamlessly across test runners and frameworks
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, "app")
__path__ = [APP_DIR]

for p in [ROOT_DIR, APP_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Execute the modern Pulse Clinic Front Desk Reception Portal
target_app = os.path.join(APP_DIR, "app.py")
with open(target_app, "r", encoding="utf-8") as f:
    exec(f.read(), globals())
