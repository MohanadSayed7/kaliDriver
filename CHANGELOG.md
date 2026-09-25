# Changelog

## v2.4.1

- Improved startup terminal clearing for Kali/XFCE and other ANSI-compatible terminals.
- Clears the visible screen and terminal scrollback before rendering the application.
- Keeps shell history and files untouched.
- Uses a fallback visual clear for unusual/non-interactive terminals.

## 2.4.0 - 2026-09-26

- Replaced randomized startup banners with a fixed Zetra ASCII project logo.
- Added the supplied `kali Driver` Zetra wordmark to the terminal startup screen.
- Kept the startup branding stable for README screenshots and project identity.
- Updated README wording to reflect the fixed logo.

## 2.3.1 - 2026-09-26

- Reworked the startup wordmark into a clean Rich-based logo layout.
- Added terminal scrollback clearing so previous shell commands are removed when supported.
- Kept randomized startup identity while avoiding broken multi-line ASCII art.
- Updated the project version metadata.

## 2.3.0 - 2026-09-26

- Simplified the main menu from 11 entries to 4 functional groups plus Exit.
- Grouped repository, update and upgrade operations under System Maintenance.
- Grouped hardware inventory, diagnostics, network and storage discovery under Hardware Diagnostics.
- Added automatic terminal clearing at startup and between major menu views.
- Added automatic `sudo` elevation when launched with `python3 kaliDriver.py`.
- Updated all usage text to support the real Python launch workflow.
- Reworked startup branding and added author/GitHub information to the banner.
- Added a third compact banner style for cleaner terminal rendering.
- Improved PCI vendor detection using PCI vendor IDs to avoid false vendor labels caused by subsystem text.
- Updated README and usage documentation.

## 2.2.0

- Added Easy Mode default startup workflow.
- `sudo ./kaliDriver.py` now checks repositories, runs APT update + upgrade, performs a full hardware diagnostic, shows recommendations, then opens the interactive menu.
- Added `--skip-maintenance` to launch directly into the menu.
- Improved `--dry-run` so repository files are not modified.

## 2.1.0

- Added APT Update and Upgrade workflows.
- Added `--update`, `--upgrade`, and `--update-upgrade` CLI commands.
- Added optional `--full-upgrade` support.
- Added menu entries for package maintenance.

## 2.0.0 - 2026-09-26

- Added randomized startup ASCII banners.
- Added generic PCI/USB driver visibility via `lspci -nnk` and `lsusb`.
- Added network interface inventory and storage inventory.
- Added vendor-aware driver and firmware recommendations.
- Added dry-run mode and non-interactive CLI flags.
- Added APT repository validation/repair with automatic backups.
- Added structured operational logging and richer diagnostics.
- Expanded common wireless, graphics and Bluetooth package profiles.
