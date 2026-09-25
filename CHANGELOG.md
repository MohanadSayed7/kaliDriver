# Changelog

## 2.5.0
- Reworked Driver & Firmware Manager around hardware-first detection.
- Detects PCI devices with no active kernel driver.
- Distinguishes an unbound device with reported kernel modules from a device with no reported driver/modules.
- Shows the affected device, PCI ID, current driver, and targeted repair profiles.
- Driver Manager now offers only profiles relevant to detected issues and asks for confirmation before installation.
- Startup diagnostics report driver issues without automatically installing drivers.
- Keeps USB devices out of false-positive "missing driver" reports because `lsusb` alone does not reliably expose kernel-driver binding.
- Updated main menu wording to describe detection and targeted repair.

## 2.4.1
- Improved terminal clearing and scrollback handling.
- Fixed startup presentation and README screenshot packaging.
