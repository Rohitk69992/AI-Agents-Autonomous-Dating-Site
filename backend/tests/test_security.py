import pytest
from app.core.security import (
    validate_and_normalize_linkedin_url,
    validate_and_normalize_instagram_url,
    is_safe_external_url,
    sanitize_text
)

def test_linkedin_url_validation():
    # Valid URLs
    valid, norm, handle = validate_and_normalize_linkedin_url("https://www.linkedin.com/in/john-doe")
    assert valid is True
    assert norm == "https://www.linkedin.com/in/john-doe"
    assert handle == "john-doe"

    valid, norm, handle = validate_and_normalize_linkedin_url("http://linkedin.com/in/janedoe123/")
    assert valid is True
    assert norm == "https://www.linkedin.com/in/janedoe123"
    assert handle == "janedoe123"

    # Invalid URLs
    valid, _, _ = validate_and_normalize_linkedin_url("https://twitter.com/in/someone")
    assert valid is False

    valid, _, _ = validate_and_normalize_linkedin_url("not-a-url")
    assert valid is False

def test_instagram_url_validation():
    # Valid URLs
    valid, norm, handle = validate_and_normalize_instagram_url("https://www.instagram.com/johndoe_travels")
    assert valid is True
    assert norm == "https://www.instagram.com/johndoe_travels"
    assert handle == "johndoe_travels"

    valid, norm, handle = validate_and_normalize_instagram_url("http://instagram.com/creative.lens/")
    assert valid is True
    assert norm == "https://www.instagram.com/creative.lens"
    assert handle == "creative.lens"

    # Invalid URLs
    valid, _, _ = validate_and_normalize_instagram_url("https://facebook.com/someone")
    assert valid is False

def test_ssrf_protection():
    # Loopback IP blocked
    safe, msg = is_safe_external_url("http://127.0.0.1:8000/secret")
    assert safe is False
    assert "prohibited" in msg

    # Link-local / AWS metadata blocked
    safe, msg = is_safe_external_url("http://169.254.169.254/latest/meta-data/")
    assert safe is False

    # Invalid protocol
    safe, msg = is_safe_external_url("ftp://example.com/file")
    assert safe is False
    assert "Unsupported protocol" in msg

def test_sanitize_text():
    raw = "<script>alert('pwned')</script>Hello World"
    cleaned = sanitize_text(raw)
    assert "<script>" not in cleaned
    assert "Hello World" in cleaned
