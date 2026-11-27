"""SSRF-Schutz für Update-Fetches: nur HTTPS, keine privaten Ziele."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class SsrfBlocked(ValueError):
    """URL abgelehnt (SSRF / unsicheres Ziel)."""


_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata",
    }
)


def _is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def validate_https_url(url: str, *, allow_unresolved: bool = False) -> str:
    """
    Erlaubt nur https:// zu öffentlichen Hosts.
    DNS-Auflösung prüft auf private/reserved Adressen.
    """
    raw = (url or "").strip()
    if not raw:
        raise SsrfBlocked("Leere URL.")
    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https":
        raise SsrfBlocked("Nur HTTPS-URLs sind erlaubt.")
    if parsed.username or parsed.password:
        raise SsrfBlocked("URLs mit Benutzerdaten sind nicht erlaubt.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise SsrfBlocked("Kein Host in der URL.")
    if host in _BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        raise SsrfBlocked(f"Host '{host}' ist gesperrt.")
    # Literal-IP im Host
    try:
        ipaddress.ip_address(host)
        if _is_private_ip(host):
            raise SsrfBlocked(f"Private/reservierte IP '{host}' ist gesperrt.")
    except ValueError:
        pass  # Hostname, keine Literal-IP

    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        if allow_unresolved:
            return raw
        raise SsrfBlocked(f"Host '{host}' nicht auflösbar.") from exc

    for info in infos:
        sockaddr = info[4]
        ip = sockaddr[0]
        if _is_private_ip(ip):
            raise SsrfBlocked(f"Aufgelöste Adresse '{ip}' für '{host}' ist privat/gesperrt.")

    return raw
