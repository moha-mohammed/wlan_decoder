# 📡 WLAN DECODER // v2.0
> Offline terminal utility for scanning WiFi networks and decoding `fh_` prefixed SSIDs.  
> Styled after professional Kali Linux security tools. Fully cross-platform.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Win%20%7C%20Linux%20%7C%20Termux-lightgrey.svg)](README.md)

## 📋 Features
- 🔒 **100% Offline** – No internet or cloud dependencies required
- 🖥️ **Cross-Platform** – Native support for Windows, Linux, and Android Termux
- 🎛️ **Interactive TUI** – Clean menu system with ANSI/Kali-style theming
- ⚡ **Direct CLI Mode** – Bypass menu with `--decode` flag
- 🛡️ **Zero Dependencies** – Pure Python 3.8+ standard library
- 📶 **Platform-Aware Scanning** – Auto-adapts to `netsh` (Win), `nmcli`/`iw` (Linux), or manual fallback (Termux)

## 📦 Prerequisites
- Python 3.8 or higher
- Administrator/Root privileges *(required for WiFi scanning on most systems)*
- Termux + Termux:API *(Android only, for optional enhanced scanning)*

## 🚀 Run Instructions

### 🪟 Windows Desktop
```powershell
# Administrator PowerShell recommended for netsh scan
python wlan_decoder.py


🐧 **Linux Desktop**

# Install nmcli if missing:
sudo apt install network-manager   # Debian/Ubuntu
sudo pacman -S networkmanager      # Arch

# Run:
sudo python3 wlan_decoder.py

# Or without sudo (nmcli may work as normal user):
python3 wlan_decoder.py


🤖 **Android Termux**

# One-time setup:
pkg update && pkg install python termux-api
# Also install 'Termux:API' from F-Droid (not Play Store)

# Run:
python wlan_decoder.py

# Single decode:
python wlan_decoder.py --decode fh_7850

# Single decode without menu:
python wlan_decoder.py --decode fh_7850
