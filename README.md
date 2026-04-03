📡 WLAN DECODER // v2.0
Offline terminal utility for scanning WiFi networks and decoding fh_ prefixed SSIDs.
Styled after professional Kali Linux security tools. Fully cross-platform.
📋 Features
🔒 100% Offline – No internet or cloud dependencies required
🖥️ Cross-Platform – Native support for Windows, Linux, and Android Termux
🎛️ Interactive TUI – Clean menu system with ANSI/Kali-style theming
⚡ Direct CLI Mode – Bypass menu with --decode flag
🛡️ Zero Dependencies – Pure Python 3.8+ standard library
📶 Platform-Aware Scanning – Auto-adapts to netsh (Win), nmcli/iw (Linux), or manual fallback (Termux)
📦 Prerequisites
Python 3.8 or higher
Administrator/Root privileges (required for WiFi scanning on most systems)
Termux + Termux:API (Android only, for optional enhanced scanning)
🚀 Run Instructions
🪟 Windows Desktop
powershell
12345
🐧 Linux Desktop
bash
123456789
🤖 Android Termux
bash
123456789
🛠️ CLI Reference
Flag
Description
--decode <SSID>
Skip menu & directly decode an fh_ prefixed SSID
--help
Show usage information & exit
--version
Display tool version & exit
⚠️ Important Notes
Permissions: WiFi scanning requires elevated privileges on Windows (netsh) and Linux (iw/nmcli). Run as Administrator/root for full functionality.
Termux Limitations: Android restricts direct WiFi scanning. The tool gracefully falls back to manual input if termux-wifi-scaninfo is unavailable.
Offline-First: This tool performs zero network requests. All logic runs locally on your device.
Mapping Logic: Decodes using strict bidirectional substitution: 1↔e, 2↔d, 3↔c, 4↔b, 5↔a, 6↔9, 7↔8, 0↔f. Output format: wlan<decoded_string>.
📜 Disclaimer
This tool is intended for educational purposes, authorized security testing, and personal network management only. The author assumes no liability for misuse. Always obtain explicit permission before scanning or interacting with networks you do not own.
