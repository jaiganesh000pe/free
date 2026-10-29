import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
    EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "brevo")  # "brevo" (HTTPS API) or "smtp"
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")  # must be a verified sender in Brevo
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SENDER_NAME = os.getenv("SENDER_NAME", "Recruiting")
    SENDER_ADDRESS = os.getenv("SENDER_ADDRESS", "")  # physical address (CAN-SPAM)
    SEND_PER_MINUTE = int(os.getenv("SEND_PER_MINUTE", "60"))
    DAILY_CAP = int(os.getenv("DAILY_CAP", "300"))
    TARGET_CANDIDATES = int(os.getenv("TARGET_CANDIDATES", "400"))
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
