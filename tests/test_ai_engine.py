import os
import builtins
from ai_engine import generate_cold_email


def test_generate_cold_email_logs(tmp_path, monkeypatch):
    # redirect any file writes to a temporary log
    monkeypatch.setenv("OLLAMA_MODEL", "dummy")

    # create a dummy subprocess.run that returns predictable output
    class Dummy:
        stdout = "Subject: test\nBody"
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Dummy())

    # intercept open() so ai_engine writes to our temp file instead
    log_path = tmp_path / "ai_generation.log"
    def fake_open(path, mode="r", encoding=None, **kwargs):
        # ignore proper path passed, always open our temp log
        return builtins.open(log_path, mode, encoding=encoding, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    lead = {"name": "Bob", "niche": "niche", "industry": "industry"}
    result = generate_cold_email(lead)
    assert "Subject" in result

    # now read from the temp log file
    with open(log_path) as f:
        content = f.read()
    assert "Subject: test" in content
