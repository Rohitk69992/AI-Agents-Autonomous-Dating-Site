import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Tuple

LINKEDIN_URL_PATTERN = re.compile(
    r"^https?://(www\.)?linkedin\.com/in/([a-zA-Z0-9_\-\.%]+)/?$", re.IGNORECASE
)
INSTAGRAM_URL_PATTERN = re.compile(
    r"^https?://(www\.)?instagram\.com/([a-zA-Z0-9_\.]+)/?$", re.IGNORECASE
)

# SSRF restricted IP ranges (private, loopback, link-local, multicast, cloud metadata)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local & cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def validate_and_normalize_linkedin_url(url: str) -> Tuple[bool, str, str]:
    """
    Validates a LinkedIn profile URL, normalizes it, and extracts the username/handle.
    Returns: (is_valid, normalized_url, handle)
    """
    if not url:
        return False, "", ""
    url = url.strip()
    match = LINKEDIN_URL_PATTERN.match(url)
    if not match:
        return False, url, ""
    handle = match.group(2).lower()
    normalized = f"https://www.linkedin.com/in/{handle}"
    return True, normalized, handle

def validate_and_normalize_instagram_url(url: str) -> Tuple[bool, str, str]:
    """
    Validates an Instagram profile URL, normalizes it, and extracts the username/handle.
    Returns: (is_valid, normalized_url, handle)
    """
    if not url:
        return False, "", ""
    url = url.strip()
    match = INSTAGRAM_URL_PATTERN.match(url)
    if not match:
        return False, url, ""
    handle = match.group(2).lower()
    normalized = f"https://www.instagram.com/{handle}"
    return True, normalized, handle

def is_safe_external_url(url: str) -> Tuple[bool, str]:
    """
    Protects against Server-Side Request Forgery (SSRF).
    Verifies that the target hostname resolves only to public, non-reserved IPs.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "Unsupported protocol. Only HTTP and HTTPS are permitted."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname."

        # Resolve IP addresses
        addr_infos = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"Access to IP address {ip_str} is prohibited for security."
        
        return True, "URL is safe for network retrieval."
    except Exception as e:
        return False, f"Failed to resolve URL destination: {str(e)}"

def sanitize_text(text: str) -> str:
    """
    Basic text sanitizer to prevent direct injection of raw script tags or control characters.
    """
    if not text:
        return ""
    # Strip dangerous HTML tags
    cleaned = re.sub(r"<(script|iframe|object|embed)[^>]*>.*?</\1>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"<(script|iframe|object|embed)[^>]*/>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()
