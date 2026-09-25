from ipaddress import ip_address
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import socket
from ..config import settings

TRACKING_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}

def normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    scheme = "https" if parts.scheme.lower() in {"http", "https"} else parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    port = parts.port
    netloc = hostname
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    query = urlencode([(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True) if key.lower() not in TRACKING_KEYS])
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, query, ""))

def validate_public_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Only absolute HTTP(S) URLs are allowed")
    hostname = parts.hostname.lower()
    local_demo = settings.allow_local_demo_targets and hostname in {"localhost", "127.0.0.1"}
    if not local_demo and (hostname in {"localhost", "metadata.google.internal"} or hostname.endswith(".localhost")):
        raise ValueError("Private or local hosts are not allowed")
    try:
        addresses = {ip_address(hostname)}
    except ValueError:
        addresses = {ip_address(info[4][0]) for info in socket.getaddrinfo(hostname, None)}
    if not local_demo and any(address.is_private or address.is_loopback or address.is_link_local or address.is_reserved for address in addresses):
        raise ValueError("Private or local network targets are not allowed")
    return normalize_url(value)
