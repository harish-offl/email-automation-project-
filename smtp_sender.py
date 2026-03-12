import smtplib
import time
from email.mime.text import MIMEText
from config import (
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    SMTP_MAX_RETRIES,
    SMTP_RETRY_DELAY_SECONDS,
)


class SMTPSender:
    """Reusable SMTP connection for faster multi-email sending."""

    def __init__(self):
        self.server = None

    def connect(self):
        if self.server is not None:
            return
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            raise RuntimeError("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in environment.")

        self.server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
        self.server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    def close(self):
        if self.server is None:
            return
        try:
            self.server.quit()
        except Exception:
            pass
        finally:
            self.server = None

    def send(self, to_email, subject, body):
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email

        attempts = SMTP_MAX_RETRIES + 1
        last_error = None
        for attempt in range(attempts):
            try:
                self.connect()
                self.server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
                return
            except Exception as exc:
                last_error = exc
                self.close()
                if attempt < attempts - 1:
                    time.sleep(SMTP_RETRY_DELAY_SECONDS)

        raise RuntimeError(f"Failed to send to {to_email}: {last_error}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def send_email(to_email, subject, body):
    """Backward-compatible single send API."""
    with SMTPSender() as sender:
        sender.send(to_email, subject, body)
