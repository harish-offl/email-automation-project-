import concurrent.futures
import csv
import time

from smtp_sender import SMTPSender
from ai_engine import generate_cold_email
from config import DELAY_BETWEEN_EMAILS, MAX_CONCURRENT_EMAILS

# Django should already be configured by the time this module is imported


def _parse_email_content(email_content):
    lines = email_content.split("\n")
    if not lines:
        return "Growth opportunity", "Hi there,\n\nI'd like to discuss growth opportunities."
    subject = lines[0].replace("Subject: ", "").strip() or "Growth opportunity"
    body = "\n".join(lines[1:]).strip()
    if not body:
        body = "Hi there,\n\nI'd like to discuss growth opportunities."
    return subject, body


def _load_leads(use_csv_fallback=True):
    from app.models import Lead

    leads = []
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

    if not leads and use_csv_fallback:
        try:
            with open("leads.csv") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    leads.append(row)
        except FileNotFoundError:
            print("No leads.csv file found and no leads in database")
            return
    elif not leads:
        print("No leads found in database; campaign not started")
        return

    return leads


def _split_chunks(items, chunk_count):
    chunk_count = max(1, min(chunk_count, len(items)))
    chunks = [[] for _ in range(chunk_count)]
    for idx, item in enumerate(items):
        chunks[idx % chunk_count].append(item)
    return [chunk for chunk in chunks if chunk]


def _process_chunk(worker_id, rows):
    sent = 0
    skipped = 0
    failed = 0

    with SMTPSender() as sender:
        for row in rows:
            solution = (row.get("niche") or "").strip()
            if not solution:
                skipped += 1
                print(f"[worker-{worker_id}] Skipped {row.get('email', 'unknown')}: missing solution/niche")
                continue

            try:
                email_content = generate_cold_email(row)
                subject, body = _parse_email_content(email_content)
                sender.send(row["email"], subject, body)
                sent += 1
                print(f"[worker-{worker_id}] Email sent to: {row['email']}")
            except Exception as exc:
                failed += 1
                print(f"[worker-{worker_id}] Failed {row.get('email', 'unknown')}: {exc}")

            if DELAY_BETWEEN_EMAILS > 0:
                time.sleep(DELAY_BETWEEN_EMAILS)

    return sent, skipped, failed


def run_campaign(use_csv_fallback=True):
    """Send generated cold emails to leads with parallel workers."""
    leads = _load_leads(use_csv_fallback=use_csv_fallback)
    if not leads:
        return

    worker_count = max(1, min(MAX_CONCURRENT_EMAILS, len(leads)))
    chunks = _split_chunks(leads, worker_count)

    started_at = time.perf_counter()
    total_sent = 0
    total_skipped = 0
    total_failed = 0

    if worker_count == 1:
        sent, skipped, failed = _process_chunk(1, chunks[0])
        total_sent += sent
        total_skipped += skipped
        total_failed += failed
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(_process_chunk, idx + 1, chunk)
                for idx, chunk in enumerate(chunks)
            ]
            for future in concurrent.futures.as_completed(futures):
                sent, skipped, failed = future.result()
                total_sent += sent
                total_skipped += skipped
                total_failed += failed

    elapsed = max(0.001, time.perf_counter() - started_at)
    throughput = total_sent / elapsed
    print(
        f"Campaign complete: sent={total_sent}, skipped={total_skipped}, failed={total_failed}, "
        f"workers={worker_count}, elapsed={elapsed:.2f}s, throughput={throughput:.2f} emails/sec"
    )
