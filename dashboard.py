#!/usr/bin/env python3
"""Server-Framework — unified control center (canonical launcher).

A single, branded entry point that ties the real Core/Web/Admin modules together:

  * System status .......... Core/SysMonitor.Sensor (CPU/mem/disk/temp/uptime)
  * Modes & processes ...... Core/Modes.ModeManager + Core/Engine.ScriptEngine
  * Path registry .......... Core/Settings.Path_Settings + Core/DirectoryManager
  * Server launchers ....... prints exact commands for the Admin/Web/FTP servers
  * Recent logs ............ tails the newest files under Logs/

Modes
-----
  python3 dashboard.py            interactive, branded menu loop
  python3 dashboard.py --demo     scripted, non-interactive showcase (exits 0)
  python3 dashboard.py --help     argparse help

Robustness: EOF/pipe-safe (``dashboard.py < /dev/null`` exits promptly), all
server work is delegated via printed commands so nothing ever blocks, and rich
is optional (clean ANSI fallback when it is missing).
"""
import argparse
import os
import sys

# --- sys.path: Core modules use flat imports (``from Log import Logs``) ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
for _sub in ("Core", "Web", "Admin"):
    _p = os.path.join(PROJECT_ROOT, _sub)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

PY = sys.executable or "python3"
LOGS_DIR = os.path.join(PROJECT_ROOT, "Logs")

BRAND = "SERVER-FRAMEWORK"
TAGLINE = "Unified control center for modes, processes, sensors & servers"

# --------------------------------------------------------------------------- #
#  Presentation layer: rich if available, otherwise a tidy ANSI fallback.
# --------------------------------------------------------------------------- #
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich.prompt import Prompt
    from rich import box

    _console = Console()
    RICH = True
except Exception:  # pragma: no cover - exercised only when rich is absent
    _console = None
    RICH = False

# Plain ANSI colors for the fallback path.
_C = {
    "cyan": "\033[36m", "green": "\033[32m", "red": "\033[31m",
    "yellow": "\033[33m", "magenta": "\033[35m", "blue": "\033[34m",
    "bold": "\033[1m", "dim": "\033[2m", "reset": "\033[0m",
}


def _plain(s):
    return f"{s}"


def out(msg=""):
    if RICH:
        _console.print(msg)
    else:
        print(msg)


def rule(title=""):
    if RICH:
        _console.print(Rule(f"[bold cyan]{title}[/]" if title else ""))
    else:
        line = "-" * 66
        if title:
            print(f"{_C['cyan']}{_C['bold']}-- {title} {line[len(title) + 4:]}{_C['reset']}")
        else:
            print(f"{_C['dim']}{line}{_C['reset']}")


def ok(msg):
    if RICH:
        _console.print(f"[bold green]✓[/] {msg}")
    else:
        print(f"{_C['green']}✓{_C['reset']} {msg}")


def err(msg):
    if RICH:
        _console.print(f"[bold red]✗[/] {msg}")
    else:
        print(f"{_C['red']}✗{_C['reset']} {msg}")


def info(msg):
    if RICH:
        _console.print(f"[cyan]›[/] {msg}")
    else:
        print(f"{_C['cyan']}›{_C['reset']} {msg}")


def banner():
    if RICH:
        title = Text(BRAND, style="bold cyan")
        sub = Text(TAGLINE, style="dim")
        body = Text.assemble(title, "\n", sub)
        _console.print(Panel(body, box=box.DOUBLE, border_style="cyan",
                             padding=(1, 4)))
    else:
        bar = "=" * 62
        print(f"{_C['cyan']}{bar}{_C['reset']}")
        print(f"{_C['cyan']}{_C['bold']}  {BRAND}{_C['reset']}")
        print(f"{_C['dim']}  {TAGLINE}{_C['reset']}")
        print(f"{_C['cyan']}{bar}{_C['reset']}")


# --------------------------------------------------------------------------- #
#  Quick status snapshot (fast, non-blocking) for the summary panel.
# --------------------------------------------------------------------------- #
def quick_status():
    """Return a small dict of headline metrics using psutil directly."""
    data = {}
    try:
        import psutil
        import platform
        import time
        import datetime
        data["cpu"] = f"{psutil.cpu_percent(interval=None):.0f}%"
        vm = psutil.virtual_memory()
        data["mem"] = f"{vm.percent:.0f}%  ({vm.used / 1024**3:.1f}/{vm.total / 1024**3:.1f} GB)"
        du = psutil.disk_usage("/")
        data["disk"] = f"{du.percent:.0f}%  ({du.used / 1024**3:.0f}/{du.total / 1024**3:.0f} GB)"
        up = int(time.time() - psutil.boot_time())
        data["uptime"] = str(datetime.timedelta(seconds=up))
        data["host"] = f"{platform.node()} · {platform.system()} {platform.release()}"
    except Exception as e:  # pragma: no cover
        data["error"] = str(e)
    return data


def status_panel():
    s = quick_status()
    rows = [
        ("Host", s.get("host", "?")),
        ("CPU", s.get("cpu", "?")),
        ("Memory", s.get("mem", "?")),
        ("Disk /", s.get("disk", "?")),
        ("Uptime", s.get("uptime", "?")),
    ]
    if RICH:
        t = Table.grid(padding=(0, 2))
        t.add_column(style="cyan", justify="right")
        t.add_column(style="white")
        for k, v in rows:
            t.add_row(k, str(v))
        _console.print(Panel(t, title="[bold]live snapshot[/]",
                             border_style="green", box=box.ROUNDED))
    else:
        print(f"{_C['green']}[ live snapshot ]{_C['reset']}")
        for k, v in rows:
            print(f"   {_C['cyan']}{k:>8}{_C['reset']}  {v}")


# --------------------------------------------------------------------------- #
#  Menu actions — every one drives a REAL project capability.
# --------------------------------------------------------------------------- #
def action_system_status():
    """Full sensor sweep via Core/SysMonitor.Sensor."""
    rule("System status  ·  Core/SysMonitor.Sensor")
    try:
        from SysMonitor import Sensor
        s = Sensor()
        s.Uptime()
        s.CPU_Checker()
        s.Memory_Checker()
        s.Disk_Checker()
        s.Component_Temp_Checker()
        ok("Sensor sweep complete")
    except Exception as e:
        err(f"Sensor error: {e}")


def action_modes_processes():
    """Detected terminals + managed modes + process registry (no spawning)."""
    rule("Modes & processes  ·  Core/Modes + Core/Engine")
    try:
        from Settings import Server_Settings
        from Modes import ModeManager
        from DirectoryManager import ProcessManager

        system = Server_Settings.check_system()
        terminals = sorted(Server_Settings.get_available_terminals(system))
        info(f"Platform: {system}")
        info("Detected terminals: " + (", ".join(terminals) if terminals else "none"))

        modes = ModeManager().list_modes()
        if RICH:
            t = Table(box=box.SIMPLE, border_style="cyan")
            t.add_column("#", style="magenta", justify="right")
            t.add_column("Managed mode", style="white")
            for i, m in enumerate(modes, 1):
                t.add_row(str(i), m)
            _console.print(t)
        else:
            for i, m in enumerate(modes, 1):
                print(f"   [{i}] {m}")

        registry = ProcessManager().ReadProcesses()
        info(f"Process registry (ProcessesLab.json): {len(registry)} tracked process(es)")
        for name, meta in registry.items():
            print(f"   • {name}: PID {meta.get('Process ID')} in {meta.get('Used Terminal')}")

        # Engine's live view of tracked scripts (empty on a fresh control center).
        from Engine import ScriptEngine
        ScriptEngine().show_running()
        ok(f"{len(modes)} mode(s) detected, {len(registry)} process(es) in registry")
    except Exception as e:
        err(f"Modes/process error: {e}")


def action_path_registry():
    """Resolved project paths via Core/Settings + Core/DirectoryManager."""
    rule("Path registry  ·  Core/Settings.Path_Settings + Paths.json")
    try:
        from Settings import Path_Settings
        ps = Path_Settings()
        keys = [
            "Server-FrameworkPath", "Server-FrameworkCore", "Server-FrameworkLogs",
            "Server-FrameworkWeb", "Server-FrameworkAdmin", "Server-FrameworkOther",
        ]
        if RICH:
            t = Table(box=box.SIMPLE, border_style="cyan")
            t.add_column("Key", style="cyan")
            t.add_column("Resolved path", style="white")
            for k in keys:
                t.add_row(k, ps.checkpath(k) or "[dim]unresolved[/]")
            _console.print(t)
        else:
            for k in keys:
                print(f"   {_C['cyan']}{k:<24}{_C['reset']} {ps.checkpath(k) or '(unresolved)'}")
        ok("Path registry resolved from Core/Paths.json")
    except Exception as e:
        err(f"Path registry error: {e}")


def action_launchers():
    """Print the exact commands to start the servers (never blocks)."""
    rule("Server launchers  ·  copy/paste to start")
    launchers = [
        ("Admin socket server", f"{PY} Admin/AdminPanel.py", "auth + IP-ban TCP panel (localhost:3000)"),
        ("Admin client", f"{PY} Admin/Admin.py", "connect to the socket panel"),
        ("Flask web dashboard", f"{PY} Web/Web_Backend.py --host 127.0.0.1 --port 5000",
         "browser UI (add --debug for local dev only)"),
        ("FTP file server", f"{PY} Other/FTP/ftp_server.py --path ./shared --host 127.0.0.1 --port 2121",
         "pyftpdlib share (user/test by default)"),
    ]
    if RICH:
        t = Table(box=box.MINIMAL_HEAVY_HEAD, border_style="yellow")
        t.add_column("Service", style="bold yellow")
        t.add_column("Command", style="green")
        t.add_column("Notes", style="dim")
        for name, cmd, note in launchers:
            t.add_row(name, cmd, note)
        _console.print(t)
    else:
        for name, cmd, note in launchers:
            print(f"   {_C['yellow']}{name}{_C['reset']}")
            print(f"      {_C['green']}{cmd}{_C['reset']}")
            print(f"      {_C['dim']}{note}{_C['reset']}")
    info("These are printed, not executed — the control center never blocks on a server.")


def action_view_logs(tail_lines=12):
    """List Logs/ and tail the most-recently-modified log file."""
    rule("Recent logs  ·  Logs/")
    try:
        if not os.path.isdir(LOGS_DIR):
            err("Logs/ directory not found")
            return
        logs = [os.path.join(LOGS_DIR, f) for f in os.listdir(LOGS_DIR)
                if f.endswith(".log") and os.path.isfile(os.path.join(LOGS_DIR, f))]
        logs.sort(key=os.path.getmtime, reverse=True)
        if not logs:
            info("No .log files yet.")
            return
        info(f"{len(logs)} log file(s); newest first:")
        for lf in logs[:8]:
            size = os.path.getsize(lf)
            print(f"   • {os.path.basename(lf):<28} {size:>7} bytes")

        newest = logs[0]
        rule(f"tail · {os.path.basename(newest)}")
        with open(newest, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()[-tail_lines:]
        if not lines:
            info("(empty)")
        for line in lines:
            print("   " + line.rstrip())
        ok(f"Tailed {os.path.basename(newest)}")
    except Exception as e:
        err(f"Log view error: {e}")


# --------------------------------------------------------------------------- #
#  Interactive menu loop (EOF / pipe safe).
# --------------------------------------------------------------------------- #
MENU = [
    ("System status (CPU/mem/disk/temp/uptime)", action_system_status),
    ("Modes & processes (terminals, registry)", action_modes_processes),
    ("Path registry (resolved project paths)", action_path_registry),
    ("Server launchers (print start commands)", action_launchers),
    ("View recent logs", action_view_logs),
]


def render_menu():
    if RICH:
        t = Table(box=box.SIMPLE_HEAVY, border_style="cyan", show_header=False)
        t.add_column(style="bold magenta", justify="right")
        t.add_column(style="white")
        for i, (label, _) in enumerate(MENU, 1):
            t.add_row(str(i), label)
        t.add_row("q", "[dim]quit[/]")
        _console.print(Panel(t, title="[bold cyan]menu[/]", border_style="cyan"))
    else:
        print(f"\n{_C['cyan']}{_C['bold']}menu{_C['reset']}")
        for i, (label, _) in enumerate(MENU, 1):
            print(f"   {_C['magenta']}{i}{_C['reset']}  {label}")
        print(f"   {_C['magenta']}q{_C['reset']}  quit")


def prompt_choice():
    """Read a menu choice. Returns None on EOF / non-interactive stdin."""
    try:
        if RICH:
            return Prompt.ask("[bold cyan]select[/]").strip()
        return input("select > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None


def interactive():
    banner()
    status_panel()
    if not sys.stdin.isatty():
        info("stdin is not a TTY — nothing to read interactively. "
             "Try 'dashboard.py --demo'.")
        return 0
    while True:
        render_menu()
        choice = prompt_choice()
        if choice is None:
            out()
            info("Bye.")
            return 0
        if choice.lower() in ("q", "quit", "exit"):
            info("Bye.")
            return 0
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            out()
            MENU[int(choice) - 1][1]()
        else:
            err(f"Unknown choice: {choice!r}")


# --------------------------------------------------------------------------- #
#  --demo : scripted, non-interactive, runs the real features and exits 0.
# --------------------------------------------------------------------------- #
def demo(as_json=False):
    banner()
    info("Running scripted showcase of REAL features (non-interactive)\n")
    status_panel()

    action_system_status()
    out()
    action_modes_processes()
    out()
    action_path_registry()
    out()
    action_launchers()
    out()
    action_view_logs(tail_lines=6)

    rule("Demo summary")
    summary = {}
    try:
        from Modes import ModeManager
        from DirectoryManager import ProcessManager
        from Settings import Server_Settings, Path_Settings
        summary["modes_detected"] = len(ModeManager().list_modes())
        summary["terminals_detected"] = len(
            Server_Settings.get_available_terminals(Server_Settings.check_system()))
        summary["processes_tracked"] = len(ProcessManager().ReadProcesses())
        summary["project_root"] = Path_Settings().checkpath("Server-FrameworkPath")
        summary["log_files"] = len([f for f in os.listdir(LOGS_DIR) if f.endswith(".log")]) \
            if os.path.isdir(LOGS_DIR) else 0
    except Exception as e:  # pragma: no cover
        summary["error"] = str(e)

    if as_json:
        import json
        print(json.dumps(summary, indent=2))
    else:
        for k, v in summary.items():
            info(f"{k}: {v}")
    ok("Demo complete — all features exercised, no servers left running.")
    return 0


# --------------------------------------------------------------------------- #
#  Entry point.
# --------------------------------------------------------------------------- #
def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="dashboard.py",
        description=f"{BRAND} — {TAGLINE}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--demo", action="store_true",
                        help="run a scripted non-interactive showcase and exit 0")
    parser.add_argument("--json", action="store_true",
                        help="with --demo, print the summary as JSON")
    args = parser.parse_args(argv)

    try:
        if args.demo:
            return demo(as_json=args.json)
        return interactive()
    except KeyboardInterrupt:
        out()
        info("Interrupted.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
