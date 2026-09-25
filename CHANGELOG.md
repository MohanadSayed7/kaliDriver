# Changelog

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
