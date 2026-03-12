import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

DELAY_BETWEEN_EMAILS = float(os.getenv("DELAY_BETWEEN_EMAILS", "10"))
MAX_CONCURRENT_EMAILS = max(1, int(os.getenv("MAX_CONCURRENT_EMAILS", "2")))
SMTP_MAX_RETRIES = max(0, int(os.getenv("SMTP_MAX_RETRIES", "2")))
SMTP_RETRY_DELAY_SECONDS = float(os.getenv("SMTP_RETRY_DELAY_SECONDS", "1.5"))
