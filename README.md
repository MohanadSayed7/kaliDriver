# kaliDriver 3.0

**Hardware, Driver, Firmware & System Maintenance Assistant for Kali Linux**

`kaliDriver` is designed around a simple workflow:

> **Scan → Identify exact hardware → Resolve safe driver/firmware actions → Install → Verify → Reboot when required**

It is not a static list of vendor drivers. The tool inspects PCI/USB hardware, kernel driver binding, firmware errors, packages, DKMS and the running kernel before proposing repairs.

## Main menu

```text
[1] Scan missing drivers & firmware
[2] Install All + Update & Upgrade
[3] Install Missing Drivers
[4] Update & Upgrade System
[5] Full Hardware & Driver Scan
[0] Exit
```

### 1 — Scan Missing Drivers & Firmware

Read-only diagnosis. It does **not** install anything.

The scan checks:

- PCI hardware IDs with `lspci -nnk`
- USB hardware IDs with `lsusb`
- active kernel driver binding
- advertised kernel modules
- GPU / network / Bluetooth device classes
- kernel firmware errors from `dmesg`
- safe hardware-ID-to-package mappings

### 2 — Install All + Update & Upgrade

Full repair workflow:

1. Validate Kali repositories.
2. Run `apt update`.
3. Run `apt full-upgrade`.
4. Scan hardware again.
5. Resolve exact missing drivers/firmware.
6. Install only packages mapped to detected hardware.
7. Verify hardware and kernel state.
8. Reboot when `/var/run/reboot-required` indicates it is necessary.

`Install All` means **all safe repairs detected for this machine**, not every driver package available in Kali.

### 3 — Install Missing Drivers

Installs only the safely resolved missing driver/firmware packages. It does not perform a full system upgrade first.

### 4 — Update & Upgrade System

Runs Kali package maintenance and then performs a driver/kernel verification pass.

### 5 — Full Hardware & Driver Scan

Displays the complete hardware inventory plus the repair analysis.

## Hardware-ID resolution

Driver decisions are based on exact device IDs where possible. For example, Broadcom BCM43142 Wi-Fi uses PCI ID `14e4:4365` and is mapped to `broadcom-sta-dkms` instead of blindly installing a generic Broadcom firmware package.

Unknown hardware is reported for manual diagnosis rather than being assigned a potentially incompatible driver.

## Firmware diagnostics

`kaliDriver` also reads kernel firmware errors such as `failed to load` and `firmware patch file not found`.

Some firmware is distributed as a device-specific artifact rather than a normal generic APT package. Those cases are explicitly reported instead of pretending that a generic package fixed the device.

## GPU detection

The scanner identifies display devices such as:

- Intel graphics
- AMD graphics
- NVIDIA graphics

It records the PCI ID and active kernel driver (for example `i915`, `amdgpu`, or `nouveau`) and uses that information during verification.

## Safety model

- No driver is installed merely because a vendor name was detected.
- Exact hardware mappings take priority over generic vendor heuristics.
- Unknown mappings are shown as requiring manual diagnosis.
- Package installation uses APT rather than downloading arbitrary executables.
- Repository files are backed up before `kaliDriver` changes them.
- A reboot is requested only when the system indicates one is required.

## Usage

```bash
sudo python3 kaliDriver.py
```

Read-only scan:

```bash
sudo python3 kaliDriver.py --scan
```

Full setup:

```bash
sudo python3 kaliDriver.py --setup
```

Install safely resolved missing drivers:

```bash
sudo python3 kaliDriver.py --install-missing
```

Dry run:

```bash
sudo python3 kaliDriver.py --setup --dry-run
```

## Requirements

- Kali Linux
- Python 3.10+
- root privileges
- `apt-get`
- `pciutils` / `lspci`
- `usbutils` / `lsusb`
- Rich Python package
- Internet connectivity for package operations

## Project status

Version `3.0.0` introduces the hardware-first repair architecture. The hardware database is intentionally conservative and can be expanded with verified PCI/USB ID mappings over time.

## License

MIT
