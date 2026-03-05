#!/usr/bin/env python3
"""
controlcenter_send.py - Command-line tool to send status commands to a running
Control Center instance via its TCP status server.

Usage:
    controlcenter_send [options] <command> [args...]

See man controlcenter-send(1) for full documentation.
"""

import argparse
import json
import socket
import sys


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="controlcenter-send",
        description="Send a status command to a running Control Center instance.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  set-status <indicator> <state> [message]
      Set a named status indicator.
      state: ok | warning | error | unknown

  set-message <level> <text>
      Display a message banner.
      level: info | warning | error

  clear-message
      Clear the message banner.

  reload-all
      Reload all embedded web pages.

  get-status
      Print the current state of all indicators.

  ping
      Test connectivity to the Control Center.

Examples:
  controlcenter-send set-status DAQ ok "All systems nominal"
  controlcenter-send set-status Trigger warning "High occupancy"
  controlcenter-send set-message error "Run aborted by operator"
  controlcenter-send clear-message
  controlcenter-send ping
  controlcenter-send --host ::1 --port 9876 get-status
""",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Control Center host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9876,
        help="Control Center port (default: 9876)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Connection timeout in seconds (default: 5.0)",
    )
    parser.add_argument(
        "command",
        help="Command to send (see Commands above)",
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for the command",
    )
    return parser.parse_args(argv)


def build_payload(command: str, args) -> dict:
    cmd = command.lower().replace("_", "-")

    if cmd == "set-status":
        if len(args) < 2:
            sys.exit("set-status requires: <indicator> <state> [message]")
        payload = {
            "command": "set_status",
            "indicator": args[0],
            "state": args[1],
        }
        if len(args) >= 3:
            payload["message"] = " ".join(args[2:])
        return payload

    elif cmd == "set-message":
        if len(args) < 2:
            sys.exit("set-message requires: <level> <text>")
        return {
            "command": "set_message",
            "level": args[0],
            "text": " ".join(args[1:]),
        }

    elif cmd == "clear-message":
        return {"command": "clear_message"}

    elif cmd == "reload-all":
        return {"command": "reload_all"}

    elif cmd == "get-status":
        return {"command": "get_status"}

    elif cmd == "ping":
        return {"command": "ping"}

    else:
        sys.exit(f"Unknown command: {command!r}")


def connect(host: str, port: int, timeout: float) -> socket.socket:
    """Connect to host:port, supporting both IPv4 and IPv6."""
    # Use getaddrinfo so we get the right address family automatically
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    last_exc = None
    for family, socktype, proto, canonname, sockaddr in infos:
        try:
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(timeout)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last_exc = exc
            try:
                sock.close()
            except OSError:
                pass
    raise last_exc or OSError(f"Could not connect to {host}:{port}")


def main(argv=None) -> int:
    args = parse_args(argv)
    payload = build_payload(args.command, args.args)

    try:
        sock = connect(args.host, args.port, args.timeout)
    except OSError as exc:
        print(f"Error: could not connect to {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1

    with sock:
        try:
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            response = b""
            while b"\n" not in response:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        except OSError as exc:
            print(f"Error: communication failed: {exc}", file=sys.stderr)
            return 1

    try:
        result = json.loads(response.split(b"\n")[0].decode("utf-8"))
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") in ("ok", "pong") else 1
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"Error: invalid response: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
