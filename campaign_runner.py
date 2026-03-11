import csv
import time

from smtp_sender import send_email
from ai_engine import generate_cold_email
from config import DELAY_BETWEEN_EMAILS

# Django should already be configured by the time this module is imported


def run_campaign():
    """Send a uniquely generated cold email to each lead.
    Pulls leads from the Django database, falls back to CSV if DB is empty.
    """
    from app.models import Lead

    leads = []
    # Try to get leads from the database
    try:
        db_leads = Lead.objects.all()
        if db_leads.exists():
            leads = [
                {
                    "name": lead.name or "",
                    "email": lead.email,
                    "niche": lead.niche or "",
                    "industry": lead.industry or "",
                    "phone": lead.phone or "",
                    "company": lead.company or "",
                }
                for lead in db_leads
            ]
    except Exception as e:
        print(f"Could not fetch leads from DB: {e}, falling back to CSV")

    # Fallback to CSV if DB is empty or unavailable
    if not leads:
        try:
            with open("leads.csv") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    leads.append(row)
        except FileNotFoundError:
            print("No leads.csv file found and no leads in database")
            return

    for row in leads:
        email_content = generate_cold_email(row)

        lines = email_content.split("\n")
        subject = lines[0].replace("Subject: ", "")
        body = "\n".join(lines[1:])

        send_email(row["email"], subject, body)

        print("Email sent to:", row["email"])

        time.sleep(DELAY_BETWEEN_EMAILS)
