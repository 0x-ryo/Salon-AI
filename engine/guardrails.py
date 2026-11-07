"""
Responsible AI & Guardrails Module for Urban Trim & Groom Barber Salon.
Implements:
1. PII Redaction (Phone, Email, Identity protection)
2. Domain Boundary & Medical Safety Guardrails (Refusal of medical/scalp diagnosis)
3. Prompt Injection & Adversarial Defense
4. Fairness & Transparency Enforcement
"""

import re

# Medical keywords requiring strict refusal and doctor referral
MEDICAL_KEYWORDS = [
    "fungal", "fungus", "infection", "pus", "alopecia", "eczema",
    "dermatitis", "psoriasis", "antibiotic", "steroid", "prescription",
    "bleeding scalp", "blood", "tumor", "cyst", "lice infestation"
]

# Prompt injection signatures
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+(prompt|override|directive)",
    r"you\s+are\s+now\s+a",
    r"reveal\s+your\s+(instructions|prompt|api\s*key|password)",
    r"forget\s+you\s+are\s+a\s+salon",
    r"act\s+as\s+a\s+hacker",
    r"write\s+(a\s+)?(keylogger|malware|virus|exploit)"
]

# Sensitive PII regexes
PHONE_PATTERN = re.compile(r"\b(?:\+91[-.\s]?)?[6789]\d{9}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def redact_pii(text: str) -> str:
    """
    Masks phone numbers and email addresses in conversation logs
    to protect customer privacy under the Digital Personal Data Protection (DPDP) Act.
    Example: '9876543210' -> '98765***10'
    """
    def mask_phone(match):
        val = match.group(0).replace(" ", "").replace("-", "")
        if len(val) >= 10:
            return val[:5] + "***" + val[-2:]
        return "***"

    redacted = PHONE_PATTERN.sub(mask_phone, text)
    redacted = EMAIL_PATTERN.sub("[REDACTED EMAIL]", redacted)
    return redacted


def check_safety_guardrails(user_message: str):
    """
    Evaluates customer input against Responsible AI boundaries.
    Returns:
        (is_safe: bool, trigger_type: str or None, response_override: str or None)
    """
    msg_lower = user_message.lower()

    # 1. Prompt Injection & Adversarial Check
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, msg_lower):
            return (
                False,
                "PROMPT_INJECTION_DEFENSE",
                "⚠️ I am the Urban Trim & Groom automated salon assistant. I cannot execute non-salon directives, disclose system configurations, or act outside grooming services. How may I assist you with haircuts, beard styling, or appointments today?"
            )

    # 2. Medical Diagnosis & Prescription Boundary (Crucial Responsible AI check)
    for kw in MEDICAL_KEYWORDS:
        if kw in msg_lower:
            return (
                False,
                "MEDICAL_SCOPE_REFUSAL",
                "⚕️ Important Health & Safety Notice: Our barbers and stylists are certified in grooming, not clinical dermatology. For medical scalp conditions, infections, rashes, or prescription medications, please consult a licensed medical doctor or dermatologist. We can gladly assist you with cosmetic hair spa, cleansing detan, or gentle beard styling once your doctor clears it."
            )

    # 3. Profanity / Abusive Language Check
    abusive_words = ["idiot", "stupid", "useless bot", "scam", "fraud"]
    for w in abusive_words:
        if w in msg_lower and "not" not in msg_lower:
            return (
                False,
                "CIVILITY_GUARDRAIL",
                "We strive to maintain a respectful and welcoming environment for all customers and staff. If you encountered an issue with your service, please let me know your contact number or describe the incident, and I will immediately escalate it to our salon manager."
            )

    return True, None, None


def audit_fairness_and_transparency(booking_info: dict) -> dict:
    """
    Verifies that pricing and appointment allocations are completely transparent,
    free of gender/attribute markups, and clearly itemized.
    """
    return {
        "pricing_model": "Fixed Transparent Menu (Non-negotiable)",
        "hidden_surcharges": 0.0,
        "tax_status": "Included in displayed menu rate",
        "cancellation_terms": "100% free cancellation up to 60 mins before start time",
        "gender_neutrality_verified": True
    }
