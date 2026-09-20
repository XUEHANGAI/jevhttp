"""提供URL规范化和内网地址判断"""

from __future__ import annotations

import ipaddress
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


TRACKING_PARAMS = {'fbclid', 'gclid', 'mc_cid', 'mc_eid'}


def normalize_url(url: str, base: str | None = None) -> str:
    """规范化HTTP(S)地址并移除fragment和常见追踪参数"""
    value = urljoin(base, url) if base else url
    parts = urlsplit(value)
    if parts.scheme.lower() not in {'http', 'https'} or not parts.hostname:
        raise ValueError(f'只支持HTTP(S)地址: {url!r}')
    hostname = parts.hostname.lower()
    port = parts.port
    netloc = hostname
    if ':' in hostname and not hostname.startswith('['):
        netloc = f'[{hostname}]'
    if parts.username is not None:
        auth = parts.username
        if parts.password is not None:
            auth += f':{parts.password}'
        netloc = f'{auth}@{netloc}'
    if port and not (
        (parts.scheme.lower() == 'http' and port == 80)
        or (parts.scheme.lower() == 'https' and port == 443)
    ):
        netloc += f':{port}'
    query = [
        (key, query_value)
        for key, query_value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith('utm_')
        and key.lower() not in TRACKING_PARAMS
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            netloc,
            parts.path or '/',
            urlencode(query, doseq=True),
            '',
        )
    )


def is_private_host(hostname: str) -> bool:
    """判断主机是否属于本机、内网或保留地址"""
    if hostname.lower() == 'localhost':
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_reserved,
            address.is_unspecified,
        )
    )
