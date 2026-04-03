#!/usr/bin/env python3
"""
wlan_decoder.py
---------------
Offline WiFi Code Translator — ISP Internal Tool
Cross-platform: Windows, Linux, Android Termux

Usage:
    python wlan_decoder.py
    python wlan_decoder.py --help
    python wlan_decoder.py --version
"""

import argparse
import os
import platform
import re
import subprocess
import sys
import time
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION      = "2.0"
TOOL_NAME    = "wlan-decoder"
SSID_PREFIX  = "fh_"
OUT_PREFIX   = "wlan"

CHAR_MAPPING: dict[str, str] = {
    "1": "e", "e": "1",
    "2": "d", "d": "2",
    "3": "c", "c": "3",
    "4": "b", "b": "4",
    "5": "a", "a": "5",
    "6": "9", "9": "6",
    "7": "8", "8": "7",
    "0": "f", "f": "0",
}

# ---------------------------------------------------------------------------
# ANSI Colors
# ---------------------------------------------------------------------------

class C:
    GREEN   = "\033[1;32m"
    CYAN    = "\033[1;36m"
    RED     = "\033[1;31m"
    YELLOW  = "\033[1;33m"
    WHITE   = "\033[0;37m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"
    CLEAR   = "\033[2J\033[H"


def enable_ansi_colors() -> None:
    """
    Enable ANSI/VT100 escape codes on Windows via ctypes.
    No-op on Linux/macOS/Termux where they work natively.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # Enable ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004)
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        # Fallback: strip all color codes if VT unsupported
        for attr in vars(C):
            if not attr.startswith("_"):
                setattr(C, attr, "")


# ---------------------------------------------------------------------------
# Platform Detection
# ---------------------------------------------------------------------------

def detect_platform() -> str:
    """
    Detect the current operating system/environment.

    Returns:
        One of: 'windows', 'termux', 'linux', 'macos', 'unknown'
    """
    if sys.platform == "win32":
        return "windows"
    if os.environ.get("TERMUX_VERSION") or os.path.isdir("/data/data/com.termux"):
        return "termux"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    return "unknown"


def is_admin() -> bool:
    """Return True if running with elevated privileges."""
    try:
        if sys.platform == "win32":
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.geteuid() == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------

def cprint(text: str, color: str = "", end: str = "\n") -> None:
    """Print colored text and flush stdout immediately."""
    sys.stdout.write(f"{color}{text}{C.RESET}{end}")
    sys.stdout.flush()


def type_effect(text: str, color: str = C.GREEN, delay: float = 0.03) -> None:
    """Print text with a typewriter animation effect."""
    for ch in text:
        sys.stdout.write(f"{color}{ch}{C.RESET}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def separator(char: str = "─", width: int = 60, color: str = C.DIM) -> None:
    cprint(char * width, color)


def box_line(text: str, width: int = 60, color: str = C.CYAN) -> None:
    cprint(f"│  {text:<{width - 4}}│", color)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def print_banner() -> None:
    """Print ASCII art banner with tool info."""
    banner = f"""
{C.GREEN}
  ██╗    ██╗██╗      █████╗ ███╗   ██╗
  ██║    ██║██║     ██╔══██╗████╗  ██║
  ██║ █╗ ██║██║     ███████║██╔██╗ ██║
  ██║███╗██║██║     ██╔══██║██║╚██╗██║
  ╚███╔███╔╝███████╗██║  ██║██║ ╚████║
   ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝
{C.CYAN}
  ██████╗ ███████╗ ██████╗ ██████╗ ██████╗ ███████╗██████╗
  ██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
  ██║  ██║█████╗  ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
  ██║  ██║██╔══╝  ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
  ██████╔╝███████╗╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
  ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
{C.RESET}"""
    cprint(banner)

    plat  = detect_platform().upper()
    priv  = f"{C.GREEN}ADMIN ✓{C.RESET}" if is_admin() else f"{C.YELLOW}STANDARD{C.RESET}"

    cprint(f"  {C.BOLD}[ Offline WiFi Code Translator ]  v{VERSION}{C.RESET}")
    cprint(f"  {C.WHITE}Platform : {C.CYAN}{plat}{C.RESET}   "
           f"Privileges : {priv}   "
           f"Python : {C.CYAN}{sys.version.split()[0]}{C.RESET}")
    separator()
    cprint("")


# ---------------------------------------------------------------------------
# Scan Networks
# ---------------------------------------------------------------------------

def _run(cmd: list[str], timeout: int = 15) -> Optional[str]:
    """
    Run a subprocess command and return stdout as a string.
    Returns None on any failure.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            check=True,
        )
        return result.stdout.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as exc:
        code = exc.returncode
        if code in (1, 5):
            cprint(f"  [!] Permission denied (exit {code}). "
                   f"Try running as {'Administrator' if sys.platform == 'win32' else 'root/sudo'}.",
                   C.YELLOW)
        else:
            cprint(f"  [!] Command failed (exit {code}).", C.RED)
        return None
    except subprocess.TimeoutExpired:
        cprint("  [!] Scan timed out.", C.RED)
        return None
    except FileNotFoundError:
        cprint(f"  [!] Command not found: {cmd[0]}", C.RED)
        return None


def _parse_windows(raw: str) -> list[dict]:
    blocks  = re.split(r"\n(?=SSID\s+\d+\s*:)", raw, flags=re.IGNORECASE)
    ssid_re = re.compile(r"^\s*SSID\s+\d+\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    sig_re  = re.compile(r"^\s*Signal\s*:\s*(.+)$",      re.IGNORECASE | re.MULTILINE)
    seen: set[str] = set()
    networks: list[dict] = []
    for block in blocks:
        sm = ssid_re.search(block)
        if not sm:
            continue
        ssid   = re.sub(r"[\x00-\x1f\x7f\u200b\ufeff]+", "", sm.group(1)).strip()
        sig_m  = sig_re.search(block)
        signal = sig_m.group(1).strip() if sig_m else "N/A"
        if ssid and ssid not in seen:
            seen.add(ssid)
            networks.append({"ssid": ssid, "signal": signal})
    return networks


def _parse_iw(raw: str) -> list[dict]:
    networks: list[dict] = []
    seen: set[str] = set()
    current_signal = "N/A"
    for line in raw.splitlines():
        sig_m = re.search(r"signal:\s*([-\d.]+\s*dBm)", line, re.IGNORECASE)
        if sig_m:
            current_signal = sig_m.group(1).strip()
        ssid_m = re.search(r"SSID:\s*(.+)", line, re.IGNORECASE)
        if ssid_m:
            ssid = re.sub(r"[\x00-\x1f\x7f\u200b\ufeff]+", "", ssid_m.group(1)).strip()
            if ssid and ssid not in seen:
                seen.add(ssid)
                networks.append({"ssid": ssid, "signal": current_signal})
                current_signal = "N/A"
    return networks


def _parse_nmcli(raw: str) -> list[dict]:
    networks: list[dict] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        parts = line.strip().split(":")
        if len(parts) >= 1:
            ssid = re.sub(r"[\x00-\x1f\x7f\u200b\ufeff]+", "", parts[0]).strip()
            signal = parts[1].strip() if len(parts) > 1 else "N/A"
            if ssid and ssid not in seen:
                seen.add(ssid)
                networks.append({"ssid": ssid, "signal": signal})
    return networks


def scan_networks() -> list[dict]:
    """
    Scan for visible WiFi networks using OS-appropriate commands.

    Returns:
        List of {"ssid": str, "signal": str} dicts. Empty on failure.
    """
    plat = detect_platform()
    cprint(f"\n  {C.CYAN}[*] Initiating scan ({plat.upper()})...{C.RESET}")

    if not is_admin():
        cprint(f"  {C.YELLOW}[!] Not running as admin/root — scan may be incomplete.{C.RESET}")

    networks: list[dict] = []

    # ── Windows ──────────────────────────────────────────
    if plat == "windows":
        raw = _run(["netsh", "wlan", "show", "networks", "mode=Bssid"])
        if raw:
            networks = _parse_windows(raw)

    # ── Termux (Android Linux) ────────────────────────────
    elif plat == "termux":
        cprint(f"  {C.WHITE}[i] Trying nmcli...{C.RESET}")
        raw = _run(["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi"])
        if raw:
            networks = _parse_nmcli(raw)
        if not networks:
            cprint(f"  {C.WHITE}[i] nmcli failed — trying termux-wifi-scaninfo...{C.RESET}")
            raw = _run(["termux-wifi-scaninfo"])
            if raw:
                # termux-wifi-scaninfo returns JSON
                try:
                    import json
                    items = json.loads(raw)
                    seen: set[str] = set()
                    for item in items:
                        ssid = str(item.get("ssid", "")).strip()
                        lvl  = str(item.get("level", "N/A"))
                        if ssid and ssid not in seen:
                            seen.add(ssid)
                            networks.append({"ssid": ssid, "signal": f"{lvl} dBm"})
                except Exception:
                    cprint(f"  {C.RED}[!] Failed to parse termux-wifi-scaninfo output.{C.RESET}")
        if not networks:
            cprint(f"  {C.YELLOW}[!] Termux scan failed. Install termux-api:{C.RESET}")
            cprint(f"  {C.WHITE}    pkg install termux-api{C.RESET}")
            cprint(f"  {C.WHITE}    Install 'Termux:API' app from F-Droid.{C.RESET}")

    # ── Linux Desktop ─────────────────────────────────────
    elif plat in ("linux", "macos"):
        # Try nmcli first (most common on desktop Linux)
        raw = _run(["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi"])
        if raw:
            networks = _parse_nmcli(raw)

        # Fallback: iw (requires root)
        if not networks:
            cprint(f"  {C.WHITE}[i] nmcli failed — trying iw...{C.RESET}")
            # Detect wireless interface
            iface = "wlan0"
            try:
                iw_dev = _run(["iw", "dev"])
                if iw_dev:
                    m = re.search(r"Interface\s+(\S+)", iw_dev)
                    if m:
                        iface = m.group(1)
            except Exception:
                pass

            raw = _run(["iw", "dev", iface, "scan"])
            if raw:
                networks = _parse_iw(raw)

        if not networks:
            cprint(f"  {C.YELLOW}[!] Scan failed. Try: sudo python wlan_decoder.py{C.RESET}")

    else:
        cprint(f"  {C.RED}[!] Unsupported platform: {plat}{C.RESET}")

    return networks


# ---------------------------------------------------------------------------
# Display Network List
# ---------------------------------------------------------------------------

def display_networks(networks: list[dict]) -> None:
    """Print a numbered, formatted list of discovered networks."""
    separator()
    cprint(f"  {C.BOLD}{C.CYAN}DISCOVERED NETWORKS{C.RESET}")
    separator()

    if not networks:
        cprint(f"  {C.RED}No networks found.{C.RESET}\n")
        return

    fh_count = sum(1 for n in networks if n["ssid"].startswith(SSID_PREFIX))
    cprint(f"  {C.WHITE}Total: {len(networks)}   "
           f"Targets [{SSID_PREFIX}]: {C.GREEN}{fh_count}{C.RESET}\n")

    for idx, net in enumerate(networks, 1):
        ssid      = net["ssid"]
        signal    = net["signal"]
        is_target = ssid.startswith(SSID_PREFIX)
        num_col   = f"{C.CYAN}{idx:>3}.{C.RESET}"
        ssid_col  = f"{C.GREEN}{ssid}{C.RESET}" if is_target else f"{C.WHITE}{ssid}{C.RESET}"
        tag       = f" {C.GREEN}[TARGET]{C.RESET}" if is_target else ""
        sig_col   = f"{C.DIM}{signal}{C.RESET}"

        cprint(f"  {num_col}  {ssid_col}{tag}  {sig_col}")

    cprint("")


# ---------------------------------------------------------------------------
# Manual Input
# ---------------------------------------------------------------------------

def manual_input() -> str:
    """
    Prompt the user to enter an SSID manually.

    Returns:
        Stripped lowercase SSID string.
    """
    cprint(f"\n  {C.CYAN}[?] Enter target SSID:{C.RESET} ", end="")
    try:
        value = input().strip().lower()
        return value
    except (EOFError, KeyboardInterrupt):
        return ""


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def translate_code(code: str) -> tuple[Optional[str], Optional[str]]:
    """
    Translate *code* character-by-character via CHAR_MAPPING.

    Args:
        code: Extracted code string after the SSID prefix.

    Returns:
        (translated_string, None) on success.
        (None, error_message) on failure.
    """
    if not code:
        return None, "Code segment is empty."

    result: list[str] = []
    for idx, ch in enumerate(code):
        if ch not in CHAR_MAPPING:
            return None, f"Invalid character {ch!r} at position {idx}."
        result.append(CHAR_MAPPING[ch])

    return "".join(result), None


def run_decode(target: str) -> None:
    """
    Validate, translate, and display the result for *target* SSID.

    Args:
        target: Full SSID string (e.g. 'fh_7850').
    """
    separator()
    cprint(f"  {C.BOLD}{C.CYAN}DECODING TARGET{C.RESET}")
    separator()

    target = target.strip().lower()

    if not target:
        cprint(f"  {C.RED}[!] No target SSID provided.{C.RESET}\n")
        return

    cprint(f"  {C.WHITE}Target   : {C.CYAN}{target}{C.RESET}")

    if not target.startswith(SSID_PREFIX):
        cprint(f"  {C.RED}[!] Invalid SSID — must start with '{SSID_PREFIX}'.{C.RESET}\n")
        return

    code = target[len(SSID_PREFIX):]

    if not code:
        cprint(f"  {C.RED}[!] No code segment found after '{SSID_PREFIX}'.{C.RESET}\n")
        return

    cprint(f"  {C.WHITE}Code     : {C.YELLOW}{code}{C.RESET}")
    cprint(f"  {C.WHITE}Running translation", end="")

    for _ in range(3):
        time.sleep(0.25)
        sys.stdout.write(f"{C.CYAN}.{C.RESET}")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    translated, error = translate_code(code)

    if error:
        cprint(f"\n  {C.RED}[!] Translation error: {error}{C.RESET}\n")
        return

    output = f"{OUT_PREFIX}{translated}"

    separator()
    sys.stdout.write(f"  {C.WHITE}Password : {C.RESET}")
    sys.stdout.flush()
    type_effect(output, color=C.GREEN, delay=0.045)
    separator()
    cprint("")


# ---------------------------------------------------------------------------
# Status Line
# ---------------------------------------------------------------------------

def print_status(target: str = "—") -> None:
    """Print a status summary line."""
    priv = "ADMIN" if is_admin() else "USER"
    plat = detect_platform().upper()
    cprint(
        f"\n  {C.DIM}[ PLATFORM: {plat} | TARGET: {target or '—'} | PRIVILEGES: {priv} ]{C.RESET}\n"
    )


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

def run_menu() -> None:
    """
    Main interactive menu loop.
    Handles scan → select → decode workflow with strict separation.
    """
    current_target: str = ""
    scanned_networks: list[dict] = []

    while True:
        print_banner()
        print_status(current_target)

        cprint(f"  {C.BOLD}{C.CYAN}┌─ MAIN MENU ───────────────────────────────────────┐{C.RESET}")
        cprint(f"  {C.CYAN}│{C.RESET}  {C.GREEN}[1]{C.RESET}  Scan Networks                                 {C.CYAN}│{C.RESET}")
        cprint(f"  {C.CYAN}│{C.RESET}  {C.GREEN}[2]{C.RESET}  Manual SSID Input                             {C.CYAN}│{C.RESET}")
        cprint(f"  {C.CYAN}│{C.RESET}  {C.GREEN}[3]{C.RESET}  Decode Target                                 {C.CYAN}│{C.RESET}")
        cprint(f"  {C.CYAN}│{C.RESET}  {C.RED}[4]{C.RESET}  Exit                                          {C.CYAN}│{C.RESET}")
        cprint(f"  {C.BOLD}{C.CYAN}└───────────────────────────────────────────────────┘{C.RESET}")

        if current_target:
            cprint(f"\n  {C.DIM}Current target: {C.GREEN}{current_target}{C.RESET}")

        cprint(f"\n  {C.CYAN}wlan-decoder{C.RESET} {C.DIM}»{C.RESET} ", end="")

        try:
            choice = input().strip()
        except (EOFError, KeyboardInterrupt):
            cprint(f"\n\n  {C.YELLOW}[!] Interrupted. Exiting.{C.RESET}\n")
            sys.exit(0)

        # ── [1] Scan ──────────────────────────────────────
        if choice == "1":
            scanned_networks = scan_networks()
            display_networks(scanned_networks)

            if scanned_networks:
                cprint(f"  {C.CYAN}[?] Select network number (or press Enter to skip):{C.RESET} ", end="")
                try:
                    sel = input().strip()
                except (EOFError, KeyboardInterrupt):
                    sel = ""

                if sel.isdigit():
                    idx = int(sel) - 1
                    if 0 <= idx < len(scanned_networks):
                        current_target = scanned_networks[idx]["ssid"]
                        cprint(f"  {C.GREEN}[✓] Target set: {current_target}{C.RESET}")
                    else:
                        cprint(f"  {C.RED}[!] Invalid selection.{C.RESET}")
                elif sel:
                    cprint(f"  {C.RED}[!] Enter a number from the list.{C.RESET}")

            _pause()

        # ── [2] Manual Input ──────────────────────────────
        elif choice == "2":
            value = manual_input()
            if value:
                current_target = value
                cprint(f"  {C.GREEN}[✓] Target set: {current_target}{C.RESET}\n")
            else:
                cprint(f"  {C.YELLOW}[!] No input provided.{C.RESET}\n")
            _pause()

        # ── [3] Decode ────────────────────────────────────
        elif choice == "3":
            if not current_target:
                cprint(f"\n  {C.YELLOW}[!] No target set. Use [1] Scan or [2] Manual Input first.{C.RESET}\n")
            else:
                run_decode(current_target)
            _pause()

        # ── [4] Exit ──────────────────────────────────────
        elif choice == "4":
            cprint(f"\n  {C.GREEN}[✓] Session terminated. Goodbye.{C.RESET}\n")
            sys.exit(0)

        else:
            cprint(f"\n  {C.RED}[!] Invalid option. Choose 1–4.{C.RESET}\n")
            time.sleep(0.8)


def _pause() -> None:
    """Wait for user to press Enter before returning to menu."""
    cprint(f"\n  {C.DIM}Press Enter to continue...{C.RESET}", end="")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Offline WiFi Code Translator — ISP Internal Tool",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{TOOL_NAME} v{VERSION}"
    )
    parser.add_argument(
        "--decode", metavar="SSID",
        help="Decode a single SSID non-interactively and exit.\n"
             "Example: python wlan_decoder.py --decode fh_7850",
    )
    args = parser.parse_args()

    enable_ansi_colors()

    # Non-interactive single decode
    if args.decode:
        enable_ansi_colors()
        run_decode(args.decode)
        sys.exit(0)

    # Interactive menu
    try:
        run_menu()
    except KeyboardInterrupt:
        cprint(f"\n\n  {C.YELLOW}[!] Interrupted. Exiting cleanly.{C.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
