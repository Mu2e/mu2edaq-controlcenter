---
title: mu2edaq-controlcenter interfaces
group: control-room
tier: A
audience: expert
summary: >
  The TCP JSON status protocol, the CLI client, the configuration
  contract and the launch contract exposed by mu2edaq-controlcenter
---

# mu2edaq-controlcenter — interfaces

The package exposes exactly one programmatic interface: a TCP status
protocol. Everything else it consumes.

## 1. Status command protocol (TCP, newline-delimited JSON)

**Endpoint** — `status_server.host`:`status_server.port`, default
`127.0.0.1:9876` (`config/controlcenter.yaml:47-48`). The port, and only
the port, is overridden by `CRS_PORT_CMD` (`src/controlcenter.py:87-89`).

**Framing** — one JSON object per line, in both directions
(`src/status_server.py:108-114`, `:137`). A connection may carry many
exchanges; the client closes it. Read timeout is 30 s
(`status_server.py:101`).

**Address family** — `host` containing `:` or equal to `""`/`"::"`
selects `AF_INET6` with `IPV6_V6ONLY=0` for dual-stack
(`status_server.py:45-60`); anything else is `AF_INET`. A bind failure
is printed and the thread exits — the GUI keeps running with no status
server, so a port clash degrades silently to "indicators can never be
set". This is the single most important operational property of the
interface.

### Requests

| `command` | Required keys | Optional | Reply |
|---|---|---|---|
| `ping` | — | — | `{"status":"pong"}` |
| `set_status` | `indicator`, `state` | `message` | `{"status":"ok"}` |
| `set_message` | `text`, `level` | — | `{"status":"ok"}` |
| `clear_message` | — | — | `{"status":"ok"}` |
| `reload_all` | — | — | `{"status":"ok"}` |
| `get_status` | — | — | `{"status":"ok","indicators":{...}}` |

`state` ∈ `ok | warning | error | unknown`.
`level` ∈ `info | warning | error`.

Unknown command → `{"status":"error","message":"Unknown command: ..."}`
(`main_window.py:365-366`). Malformed JSON →
`{"status":"error","message":"Invalid JSON: ..."}` with the connection
left open (`status_server.py:115-118`).

### Two semantics worth stating explicitly

**Underscore on the wire, hyphen on the CLI.** The protocol uses
`set_status`; `controlcenter-send` accepts `set-status` and normalizes
(`controlcenter_send.py:84`). A hand-written client must send the
underscore form. Sending `set-status` over the socket yields
`Unknown command`.

**`ok` means queued, not applied.** The four mutating commands post to
the GUI thread with `QueuedConnection` and return `{"status":"ok"}`
unconditionally (`main_window.py:319-328`). Consequently:

- `set_status` with an `indicator` that is not in `status_indicators`
  returns `ok` and changes nothing. There is no way for a client to
  learn that its indicator name is wrong except by calling `get_status`
  afterwards and comparing.
- An invalid `state` is not rejected here; the widget coerces it.

`get_status` is the only synchronous command and the only reliable
read-back.

**`ping` does not prove liveness of the UI.** It is answered inside the
server thread before the callback is reached (`status_server.py:120-122`).
A GUI whose event loop has wedged still replies `pong`, and the
`start-mu2edaq-controlcenter.sh` readiness check — which is a TCP
connect plus `ping` — will call that a successful start.

### Security

No authentication, no authorization, no TLS. Any local process can set
any indicator or clear an error banner. The loopback default is the
only control. Setting `status_server.host` to `""`, `"::"` or a
routable address exposes it to the network; nothing warns. `CRS_PORT_CMD`
cannot widen the bind, only move the port.

## 2. `controlcenter-send` — CLI client

```
controlcenter-send [--host H] [--port P] [--timeout S] <command> [args...]
```

| Option | Default | Source |
|---|---|---|
| `--host` | `127.0.0.1` | `controlcenter_send.py:56` |
| `--port` | `9876` | `controlcenter_send.py:61` |
| `--timeout` | `5.0` s | `controlcenter_send.py:67` |

Subcommands: `set-status <indicator> <state> [message...]`,
`set-message <level> <text...>`, `clear-message`, `reload-all`,
`get-status`, `ping` (`controlcenter_send.py:86-120`). Trailing
arguments are joined with spaces, so quoting a message is optional.

Note the argument order inversion between the two message-bearing
commands: `set-status` takes the message *last* (after indicator and
state) while `set-message` takes the level *first*. This is a wart, not
a bug, but it catches people.

Address resolution uses `getaddrinfo` and tries every returned family
in turn (`controlcenter_send.py:126-140`), so `--host localhost` works
whether the server bound v4 or v6.

**Exit status**: `0` if the reply's `status` is `ok` or `pong`,
otherwise `1` (`controlcenter_send.py:169`); `1` on connection failure
or invalid response. Because `ok` is returned for a discarded unknown
indicator, exit `0` does not mean the indicator changed.

`--port` does **not** read `CRS_PORT_CMD`. If the inventory moves the
port, the server follows and this client does not; the operator must
pass `--port`.

## 3. Configuration contract

`config/controlcenter.yaml`, merged over `DEFAULT_CONFIG`
(`config_loader.py:10-18`).

| Key | Type | Default | Notes |
|---|---|---|---|
| `title` | str | `"Control Center"` | window title |
| `grid.rows`, `grid.cols` | int | 2, 2 | initial grid |
| `status_indicators[]` | `{name, state}` | one `Status`/`unknown` | **defines the valid `set_status` names** |
| `pages[]` | `{name, url, position}` | `[]` | one `QWebEngineView` per entry |
| `status_server.host` | str | `127.0.0.1` | see address family above |
| `status_server.port` | int | `9876` | overridden by `CRS_PORT_CMD` |

Validation is coercive, never fatal (`config_loader.py:44-67`): a bad
state → `unknown`, a missing `url` → `about:blank`, a malformed
`position` → auto-placement. Misconfiguration surfaces as a wrong
display, not a failed start.

`position` is `[row, col]`, zero-indexed. Pages without one fill
left-to-right, top-to-bottom.

## 4. Launch contract (consumed)

The package implements the control-room start/stop contract that
`mu2edaq-controlroom-setup` pushed into every DAQ repo (recorded in
`../mu2edaq-controlroom-setup/doc/issues/03-startstop-mu2edaq-controlcenter.md`).

| Element | Value |
|---|---|
| Start script | `start-mu2edaq-controlcenter.sh` (`start.sh` → symlink) |
| Stop script | `stop-mu2edaq-controlcenter.sh` (`stop.sh` → symlink) |
| Port variable | `CRS_PORT_CMD`, from `ports: {cmd: 9876}` |
| PID file | `controlcenter.pid` |
| App id | `controlcenter` |

Both script pairs are byte-identical because the short names are
symbolic links, verified with `cmp` and `ls -l`. The long form is
canonical: it is the name in `apps.yaml` and the name symlinked into the
shared `~/controlroom/bin`, where `start.sh` would collide with every
other package. The symlinks are the one-release compatibility shim that
issue 03 asked for and can be dropped.

## 5. Consumed HTTP endpoints

Not a protocol this package defines, but a hard dependency edge:

| Cell | URL | Evidence |
|---|---|---|
| Dashboard | `http://localhost:5001` | `config/controlcenter.yaml:29` |
| Disk Watcher | `http://localhost:5002` | `config/controlcenter.yaml:32` |
| Heart Beats | `http://localhost:8081` | `config/controlcenter.yaml:35` |
| FTS | `http://localhost:5003` | `config/controlcenter.yaml:38` |

All four agree with both `apps.yaml` copies today. Nothing enforces
that. `localhost` also means the kiosk must run on the same host as all
four services — true on `shift-main`, and an unstated constraint
everywhere else.

## 6. Discovery advertisement (optional, outbound)

When `mu2edaq_discovery` is importable, the app registers a `Responder`
with `app="controlcenter"`, `scheme="tcp"`, and the resolved status port
(`src/controlcenter.py:98-101`), stopped in a `finally`
(`:108-110`). Failure to import or start is caught and printed
(`:102-103`); it never blocks startup.
