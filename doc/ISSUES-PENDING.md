# Staged issues — mu2edaq-controlcenter

Issue filing was blocked for this review wave. Each section below is the
body of one issue, ready to paste. Dedup read was performed:

```
gh issue list -R Mu2e/mu2edaq-controlcenter --state all --limit 300
#2 CLOSED  Add mu2edaq-discovery auto-discovery support
#1 CLOSED  Rename start.sh / stop.sh to start-mu2edaq-controlcenter.sh / ...
```

Both are closed and implemented in the tree (`src/controlcenter.py:96-104`;
`ls -l start.sh` shows the symlink). No fingerprint match and no
two-token title overlap with anything below, so all six are new.

---

## CC-001 — `[config] embedded dashboard URLs duplicate apps.yaml ports with no cross-check`

**Severity:** S3 — correctness or maintainability risk, no current outage
**Category:** documentation
**Location:** `config/controlcenter.yaml:29-38`
**Found by:** mega-review (`mu2e-sept-mega-review`), 2026-09-30

## What

The four grid cells embed sibling packages' ports as literal URLs. Those
same ports are declared in the shared inventory `apps.yaml`, in two
copies. Nothing ties the three together, so a port move in the inventory
leaves this file pointing at a dead port.

## Evidence

```
$ grep -n 'localhost' config/controlcenter.yaml
29:    url: "http://localhost:5001"
32:    url: "http://localhost:5002"
35:    url: "http://localhost:8081"
38:    url: "http://localhost:5003"

$ grep -n 'http:' ../mu2edaq-desktop/config/apps.yaml
38:    ports: {http: 5001, zmq: 5555}     # dashboard
67:    ports: {http: 5002}                # diskwatcher
76:    ports: {http: 5003}                # fts
85:    ports: {http: 8081, udp: 9999}     # heartbeatmonitor
```

All four agree today. The heartbeatmonitor entry carries the comment
`# http moved off 8080 (resource-manager owns it)` — evidence that ports
in this suite do move.

## Why it matters

When a port moves, the kiosk shows a connection error in that cell and
the failure looks like "the dashboard is down" to the shifter. The
inventory is the de-facto port registry for the suite but this package
is invisible to it: `apps.yaml` records that controlcenter *owns* 9876
and says nothing about the four ports it *consumes*.

This is the same root cause as the triplicated inventory filed against
`mu2edaq-desktop` (fingerprint `5a8db782`) and should be fixed with it.

## Suggested fix

Either resolve the cell URLs from `apps.yaml` at startup (the app
already reads `CRS_PORT_CMD`, so it is already inventory-aware), or add
a `consumes:` list to the inventory schema and have a consistency check
cover it. Minimum viable: a comment at `config/controlcenter.yaml:27`
naming `apps.yaml` as the authority for these four numbers.

## Related

- Inventory triplication, staged in `mu2edaq-desktop/docs/ISSUES-PENDING.md` (`5a8db782`)

<!-- mega-review-fingerprint: b871bc21 -->

---

## CC-002 — `[tests] no test suite for a package that ships a network-facing protocol`

**Severity:** S3 — correctness or maintainability risk, no current outage
**Category:** enhancement
**Location:** repository root
**Found by:** mega-review (`mu2e-sept-mega-review`), 2026-09-30

## What

There is no test suite. The package ships a six-command TCP protocol, a
coercive config loader and a cross-thread dispatch path, none of which
is covered.

## Evidence

```
$ git ls-files | grep -Ec 'test|tests/'
0
$ ls tests 2>&1
ls: tests: No such file or directory
```

`CLAUDE.md` states it plainly: "There is no test suite or linter
configured. Manual testing uses the sample configs in `config/`."

For comparison, the sibling packages in this group: `mu2edaq-desktop`
has 17 tests, `mu2edaq-controlroom-setup` has 43.

## Why it matters

Three behaviours are testable without a display and are the ones most
likely to regress:

- protocol framing and error replies (`src/status_server.py` — pure
  stdlib sockets, no Qt)
- `build_payload` command translation in `src/controlcenter_send.py:83`,
  including the hyphen/underscore mapping
- `config_loader.load_config` coercion rules (`src/config_loader.py:44-67`)

None needs PyQt6. `controlcenter_send.py` imports only stdlib, so its
tests run anywhere.

## Suggested fix

Add `tests/` with pytest covering the three above. `StatusServer` can be
driven against a stub callback on an ephemeral port; no GUI needed. Defer
`pytest-qt` for the widget layer.

## Related

- `[ci] no CI workflow` (`c653e4f3`)

<!-- mega-review-fingerprint: bad2b1c4 -->

---

## CC-003 — `[ci] no CI workflow`

**Severity:** S3 — correctness or maintainability risk, no current outage
**Category:** enhancement
**Location:** repository root
**Found by:** mega-review (`mu2e-sept-mega-review`), 2026-09-30

## What

No `.github/workflows/`. Nothing checks that the package imports, that
the YAML parses, or that the man pages are well formed.

## Evidence

```
$ ls .github/workflows 2>&1
ls: .github/workflows: No such file or directory
```

## Why it matters

The package targets Linux (AL9 control-room hosts) and is developed on
macOS. With no test suite (`bad2b1c4`) and no CI, the first execution of
any change is on the control-room wall display.

A syntax-only check would have value even before tests exist: `python -m
compileall src/`, `python -c 'import yaml,sys; yaml.safe_load(open(...))'`
on each config, and `mandoc -T lint man/man*/*`.

## Suggested fix

One workflow on push/PR: compileall, YAML parse of the five config
files, and `mandoc -T lint`. Extend to pytest once `bad2b1c4` is done.

## Related

- `[tests] no test suite ...` (`bad2b1c4`)

<!-- mega-review-fingerprint: c653e4f3 -->

---

## CC-004 — `[docs] doc/ is an empty committed directory`

**Severity:** S4 — cosmetic, stale, hygiene
**Category:** documentation
**Location:** `doc/`
**Found by:** mega-review (`mu2e-sept-mega-review`), 2026-09-30

## What

`doc/` existed on disk with no files in it, while `README.md` and
`man/man1/controlcenter.1` both referred readers to it.

## Evidence

```
$ ls -la doc/
total 0
drwxr-xr-x   2 anorman  staff   64 Mar  5  2026 .
drwxr-xr-x  20 anorman  staff  640 Jul 24 16:03 ..

$ git ls-files doc/
(no output)

$ grep -rn 'doc/' README.md man/man1/controlcenter.1
README.md:149:└── doc/                       # Additional documentation
man/man1/controlcenter.1:147:... the project documentation in \fIdoc/\fR for raw protocol details.
```

Git does not track empty directories, so the directory was untracked
local residue; a fresh clone had no `doc/` at all, and both pointers
dangled.

## Why it matters

`controlcenter.1` sends a reader looking for "raw protocol details" to a
directory that does not exist in a clone. That is the only pointer to
the protocol specification in the shipped man page.

## Suggested fix

Resolved by this review: `doc/` now holds `ARCHITECTURE.md`,
`INTERFACES.md`, `OPERATIONS.md`, `package.yaml` and this file, and the
protocol is specified in `man/man7/controlcenter-protocol.7`, which
`controlcenter.1` now cross-references. No further action.

<!-- mega-review-fingerprint: 269c8114 -->

---

## CC-005 — `[man] pages were in a flat man/ with non-conforming .TH lines`

**Severity:** S4 — cosmetic, stale, hygiene
**Category:** documentation
**Location:** `man/`
**Found by:** mega-review (`mu2e-sept-mega-review`), 2026-09-30

## What

The two man pages sat directly in `man/` rather than `man/man1/`, their
`.TH` lines used a non-standard date and manual title, and both
contained raw UTF-8 punctuation that makes `groff` emit warnings.

## Evidence

```
$ ls man/
controlcenter-send.1  controlcenter.1

$ grep -h '^.TH' man/*.1
.TH CONTROLCENTER 1 "2026-03-05" "1.0.0" "Control Center Manual"
.TH CONTROLCENTER-SEND 1 "2026-03-05" "1.0.0" "Control Center Manual"

$ groff -mandoc -Tutf8 -ww -z man/controlcenter.1
troff:man/controlcenter.1:35: warning: invalid input character code 128
troff:man/controlcenter.1:129: warning: invalid input character code 147
... (10 warnings, from U+2013/U+2014/U+201C/U+201D)
```

`man -M man controlcenter` cannot work with a flat layout; the fourth
`.TH` field should be `Mu2e DAQ Manual` and the third `<package>
<version>`.

## Why it matters

Hygiene only — `man ./man/controlcenter.1` by explicit path still
rendered. But the layout blocks `MANPATH`-based lookup, which is how the
control-room hosts expose package man pages, and the smart quotes render
as mojibake in a non-UTF-8 locale.

## Suggested fix

Done in this review: `git mv` into `man/man1/`, `.TH` normalized to the
mega-review form, UTF-8 punctuation replaced with roff escapes
(`\(em`, `\(en`, `\(lq`, `\(rq`). Both pages now pass `mandoc -T lint`
and `groff -mandoc -Tutf8 -ww -z` with no output. Three new pages were
added: `start-mu2edaq-controlcenter.sh.1`,
`stop-mu2edaq-controlcenter.sh.1` and `man7/controlcenter-protocol.7`.

The two README lines referencing the old flat paths were updated in the
same commit. Nothing else in the repository referenced `man/`.

<!-- mega-review-fingerprint: 217e1922 -->

---

## CC-006 — `[docs] CLAUDE.md claims layout is persisted on exit; closeEvent does not save`

**Severity:** S4 — cosmetic, stale, hygiene
**Category:** documentation
**Location:** `CLAUDE.md`
**Found by:** mega-review (`mu2e-sept-mega-review`), 2026-09-30

## What

`CLAUDE.md` states that layout state is written back to the config file
when the application exits. It is not. Saving is a manual menu action
to an operator-chosen file, and `closeEvent` saves nothing.

## Evidence

```
$ grep -n 'persisted' CLAUDE.md
Layout state (splitter sizes, zoom levels) is persisted back into the
config file on exit.

$ sed -n '394,398p' src/main_window.py
    def closeEvent(self, event):
        self._clock_timer.stop()
        self._server.stop()
        super().closeEvent(event)

$ sed -n '199,205p' src/main_window.py
    def _save_layout(self) -> None:
        """Save the current grid layout to a user-chosen YAML file."""
        default_dir = os.path.dirname(self._config_path)
        path, _ = QFileDialog.getSaveFileName(
```

`closeEvent` stops the clock timer and the status server, and returns.
`_save_layout` is reachable only from the "Save Layout..." menu item
(`main_window.py:164`) and writes to a path chosen in a file dialog —
never to `self._config_path`.

## Why it matters

An operator who rearranges the grid, trusts the documented behaviour and
closes the kiosk loses the arrangement. Low impact, but the doc actively
misleads.

## Suggested fix

Correct the sentence in `CLAUDE.md` to describe the actual behaviour:
layout is saved on demand via File → Save Layout to a chosen YAML file
and restored via Load Layout. (Documentation fix only — the current
behaviour is arguably the safer one for a kiosk, since it prevents an
accidental drag from permanently altering the shipped config.)

`doc/OPERATIONS.md` documents the real behaviour.

<!-- mega-review-fingerprint: 75ba5b65 -->
