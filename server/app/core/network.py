import socket

import psutil
from fastapi import Request


def list_base_urls(request: Request) -> list[str]:
    scheme = request.url.scheme
    port = request.url.port
    urls: list[str] = []
    seen: set[str] = set()

    def add(host: str | None) -> None:
        if not host:
            return
        url = f"{scheme}://{host}:{port}" if port else f"{scheme}://{host}"
        if url not in seen:
            seen.add(url)
            urls.append(url)

    add(request.url.hostname)
    for ip in _local_ipv4_addresses():
        add(ip)
    return urls


def _local_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()
    try:
        for interface_addrs in psutil.net_if_addrs().values():
            for addr in interface_addrs:
                if addr.family != socket.AF_INET or not addr.address:
                    continue
                if addr.address.startswith("169.254."):
                    continue
                if addr.address not in seen:
                    seen.add(addr.address)
                    addresses.append(addr.address)
    except OSError:
        pass
    if "127.0.0.1" not in seen:
        addresses.append("127.0.0.1")
    return addresses
