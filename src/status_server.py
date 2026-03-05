"""
status_server.py - TCP socket server that receives JSON status commands.

Protocol:
  Each message is a newline-terminated JSON object sent over TCP.

  Commands:
    { "command": "set_status", "indicator": "<name>", "state": "<ok|warning|error|unknown>",
      "message": "<optional human-readable message>" }

    { "command": "set_message", "text": "<message text>", "level": "<info|warning|error>" }

    { "command": "reload_config" }

    { "command": "ping" }   -> replies with {"status": "pong"}

  All replies are newline-terminated JSON objects.
"""

import json
import socket
import threading
from typing import Callable, Dict, Optional


class StatusServer(threading.Thread):
    """Listens on a TCP socket and dispatches incoming commands to a callback."""

    def __init__(
        self,
        host: str,
        port: int,
        command_callback: Callable[[Dict], Optional[Dict]],
    ):
        super().__init__(daemon=True, name="StatusServer")
        self.host = host
        self.port = port
        self.command_callback = command_callback
        self._server_sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        # Determine address family based on host.
        # An empty string or "::" means listen on all IPv6 interfaces (dual-stack on most OSes).
        if self.host in ("", "::") or ":" in self.host:
            family = socket.AF_INET6
            bind_host = self.host if self.host else "::"
        else:
            family = socket.AF_INET
            bind_host = self.host

        try:
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if family == socket.AF_INET6:
                # Allow dual-stack (IPv4 + IPv6) on platforms that support it
                try:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
                except (AttributeError, OSError):
                    pass
            sock.bind((bind_host, self.port))
            sock.listen(5)
            sock.settimeout(1.0)
            self._server_sock = sock
        except OSError as exc:
            print(f"[StatusServer] Failed to bind {bind_host}:{self.port}: {exc}")
            return

        print(f"[StatusServer] Listening on {bind_host}:{self.port}")
        while not self._stop_event.is_set():
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(
                target=self._handle_client,
                args=(conn, addr),
                daemon=True,
            )
            t.start()

        try:
            sock.close()
        except OSError:
            pass
        print("[StatusServer] Stopped.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass

    def _handle_client(self, conn: socket.socket, addr) -> None:
        with conn:
            buf = b""
            conn.settimeout(30.0)
            try:
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            cmd = json.loads(line.decode("utf-8"))
                        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                            resp = {"status": "error", "message": f"Invalid JSON: {exc}"}
                            self._send(conn, resp)
                            continue

                        if cmd.get("command") == "ping":
                            self._send(conn, {"status": "pong"})
                            continue

                        try:
                            result = self.command_callback(cmd)
                            if result is None:
                                result = {"status": "ok"}
                        except Exception as exc:
                            result = {"status": "error", "message": str(exc)}
                        self._send(conn, result)
            except (OSError, socket.timeout):
                pass

    @staticmethod
    def _send(conn: socket.socket, obj: Dict) -> None:
        try:
            conn.sendall((json.dumps(obj) + "\n").encode("utf-8"))
        except OSError:
            pass
