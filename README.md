# kaliDriver v3.1.0

Automatic Kali Linux hardware, driver, firmware, and system maintenance assistant.

## User workflow

The interactive UI intentionally has only two choices:

- **1 — Run**: perform the complete scan/repair/update/verify workflow automatically.
- **2 — Exit**: quit.

The program does not ask the user to choose driver profiles or enter arbitrary driver numbers.

## What Run does

1. Detect PCI and USB hardware and current kernel drivers.
2. Resolve exact known driver requirements where a safe mapping exists.
3. Refresh APT metadata.
4. Install required driver/firmware/support packages.
5. Load newly installed kernel modules when applicable.
6. Re-scan and verify the actual kernel driver state.
7. Report firmware diagnostics separately, without pretending that a firmware warning is a driver failure or that an installation succeeded when verification failed.
8. Upgrade the installed Kali system.
9. Re-verify after the upgrade.
10. Report if a reboot is required.

## Important design rule

"Install all" means **all required packages detected for this machine**, not every driver package in Kali.

The program uses conservative hardware mappings. For example, Broadcom BCM43142 PCI ID `14e4:4365` is mapped to `broadcom-sta-dkms` and `wl`. It does not blindly install a random Broadcom driver for every Broadcom device.

Firmware messages from `dmesg` are reported as diagnostics. A missing firmware filename is not automatically claimed to be fixed unless the resulting device state can be verified.

## Requirements

- Kali Linux
- Python 3.10+
- root privileges
- `apt-get`
- `pciutils` (`lspci`)
- `usbutils` (`lsusb`)
- Internet access for package installation and upgrades

Install Python dependency on Kali:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo .venv/bin/python kaliDriver.py
```

If Rich is not available, the program falls back to plain terminal output.

## Safety

The program changes installed packages, kernel modules, and system updates. Review your APT sources and keep backups of important data before major system upgrades.

License: MIT
