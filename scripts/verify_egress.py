"""Fail unless Linux kernel isolation denies outbound TCP and UDP immediately.

Run inside `docker run --network none --cap-drop ALL ...`. This verifies that
container only; it is not an outbound policy for Render or for the build phase.
"""
from __future__ import annotations

import errno
import json
from pathlib import Path
import socket
import sys


def main():
    if sys.platform != "linux":
        raise RuntimeError("Linux network namespace verification required")
    interfaces = sorted(p.name for p in Path("/sys/class/net").iterdir())
    if interfaces != ["lo"]:
        raise RuntimeError(f"Expected only loopback, got {interfaces}")
    # Prove permitted loopback still works rather than treating all socket errors
    # (including broken test setup or timeouts) as a successful isolation check.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0)); listener.listen(1)
        with socket.create_connection(listener.getsockname(), timeout=2) as client:
            peer, _ = listener.accept()
            with peer:
                client.sendall(b"local"); assert peer.recv(5) == b"local"
    results = []
    destinations = [(socket.AF_INET, "1.1.1.1", 443, "public"),
                    (socket.AF_INET, "169.254.169.254", 80, "metadata"),
                    (socket.AF_INET, "10.0.0.1", 443, "private"),
                    (socket.AF_INET6, "2606:4700:4700::1111", 443, "public_ipv6")]
    for family, host, port, label in destinations:
        for kind, protocol in [(socket.SOCK_STREAM, "tcp"), (socket.SOCK_DGRAM, "udp")]:
            with socket.socket(family, kind) as sock:
                sock.settimeout(2)
                try:
                    if kind == socket.SOCK_STREAM: sock.connect((host, port))
                    else: sock.sendto(b"egress-isolation-check", (host, port))
                except OSError as exc:
                    if exc.errno not in {errno.ENETUNREACH, errno.EHOSTUNREACH}:
                        raise RuntimeError("Unexpected error; isolation not proven") from exc
                    results.append({"destination": label, "protocol": protocol, "errno": exc.errno})
                else:
                    raise RuntimeError(f"Unauthorized outbound {protocol} destination reachable: {label}")
    print(json.dumps({"interfaces": interfaces, "loopback": "passed", "blocked": results}))


if __name__ == "__main__":
    main()
