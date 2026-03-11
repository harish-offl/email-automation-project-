import subprocess

import os

# name of the ollama model to use (must be installed locally or accessible via ollama)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")  # override with env var if needed


def generate_cold_email(lead: dict) -> str:
    """Calls the Ollama CLI to generate a unique cold email for a single lead.

    The returned text is expected to include a subject line prefixed with
    "Subject:" on the first line followed by the body.

    Args:
        lead: dictionary containing at least 'name', 'niche', and 'industry' keys.

    Returns:
        Generated email as a string.
    """
    name = lead.get("name", "there")
    niche = lead.get("niche", "your field")
    industry = lead.get("industry", "your industry")

    prompt = (
        f"Compose a cold outreach email for a {niche} business in the {industry} industry. "
        f"Address the recipient as {name} if a name is available. "
        "Create a unique subject line and message body separated by a newline. "
        "Keep the tone professional and make the email structure different from typical templates. "
        "Ensure the first line starts with 'Subject: '."
    )

    try:
        proc = subprocess.run(
            ["ollama", "generate", OLLAMA_MODEL, "--prompt", prompt],
            capture_output=True,
            text=True,
            check=True,
        )
        result = proc.stdout.strip()
    except subprocess.CalledProcessError as exc:
        # fallback to a very simple template if ollama call fails
        result = (
            f"Subject: Opportunity for {niche} in {industry}\n"
            f"Hi {name},\n\nWe thought you might be interested in ..."
        )

    # log output for auditing and potential duplicate detection
    try:
        with open("ai_generation.log", "a", encoding="utf-8") as logf:
            logf.write(result + "\n---\n")
    except Exception:
        pass

    return result
