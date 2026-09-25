# kaliDriver

**Professional Hardware, Driver & System Maintenance Assistant for Kali Linux**

`kaliDriver` is an English-language terminal utility built to make common Kali Linux hardware diagnostics, firmware management, and system maintenance easier from one interface.

## Highlights

- Fixed Zetra ASCII startup logo for a consistent project identity.
- Automatic terminal screen and scrollback cleanup before the application UI appears when supported by the terminal.
- Automatic `sudo` elevation when launched with `python3 kaliDriver.py`.
- Kali Linux and kernel detection.
- PCI inventory with active kernel-driver and device-ID information.
- USB inventory.
- Network-interface and storage inventory.
- Kali APT repository validation and repair.
- `apt update`, `apt upgrade`, and `apt full-upgrade` workflows.
- Driver and firmware profiles for common Intel, AMD, NVIDIA, Realtek, Broadcom, Qualcomm/Atheros and MediaTek hardware.
- Rich tables, panels, spinners, progress bars and colored logs.
- Dry-run mode and command-line automation options.
- Repository backups before configuration changes.

## Main Menu

The interactive menu was intentionally simplified so the main screen does not contain a long list of low-level operations:

```text
╭──────────────────────────── Main Menu ───────────────────────────╮
│  1  Hardware Diagnostics       Full hardware + network + storage │
│  2  System Maintenance         Repositories, Update, Upgrade    │
│  3  Driver & Firmware Manager  Install a recommended profile   │
│  4  System Information         Kali, kernel, Python and tools  │
│  0  Exit                       Close kaliDriver                │
╰─────────────────────────────────────────────────────────────────╯
```

Maintenance operations are grouped under **System Maintenance** instead of occupying five separate entries in the main menu.

## Screenshots

### Startup & Hardware Inventory

The screenshot below shows `kaliDriver` detecting Kali Linux and the kernel, running automatic APT maintenance, and presenting the PCI hardware inventory with vendor, kernel-driver, and device-ID information.

![kaliDriver startup and hardware inventory](docs/images/kaliDriver-startup.png)

> Screenshot captured from `kaliDriver` running on Kali Linux.

## Requirements

- Kali Linux
- Python 3.10+
- `sudo` for automatic privilege elevation
- `apt-get`
- `pciutils` (`lspci`)
- `usbutils` (`lsusb`)
- Internet access for package operations
- Python package: `rich`

## Installation

Clone the repository and install the Python dependency:

```bash
git clone https://github.com/MohanadSayed7/kaliDriver.git
cd kaliDriver
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Make the script executable if you also want to launch it as `./kaliDriver.py`:

```bash
chmod +x kaliDriver.py
```

## Usage

### Recommended — one command

```bash
python3 kaliDriver.py
```

The program automatically requests `sudo` when root privileges are required. It then:

```text
1. Clears the visible terminal
2. Shows the fixed Zetra startup logo
3. Detects Kali Linux and the kernel
4. Checks Kali firmware repositories
5. Runs APT update
6. Runs APT upgrade
7. Scans PCI and USB hardware
8. Shows driver recommendations
9. Opens the simplified main menu
```

You can also run it directly after `chmod +x`:

```bash
./kaliDriver.py
```

### Skip automatic maintenance

```bash
python3 kaliDriver.py --skip-maintenance
```

### Useful CLI commands

```bash
python3 kaliDriver.py --scan
python3 kaliDriver.py --diagnose
python3 kaliDriver.py --repo-check
python3 kaliDriver.py --repo-fix
python3 kaliDriver.py --update
python3 kaliDriver.py --upgrade
python3 kaliDriver.py --update-upgrade
python3 kaliDriver.py --full-upgrade --update-upgrade
python3 kaliDriver.py --install nvidia_gpu --dry-run
```

## Hardware Support Model

`kaliDriver` does not claim to contain a hard-coded installer for every device ever made. Instead, it uses standard Linux hardware discovery tools to inventory hardware exposed through PCI and USB, reports the kernel driver when available, and maps recognized vendor families to package-level remediation profiles.

Unknown or unusual hardware remains visible in the inventory for manual diagnosis rather than receiving an unsafe guessed driver.

## Driver & Firmware Profiles

Current profiles include:

```text
wireless_common
intel_wireless
realtek_wireless
atheros_wireless
broadcom_wireless
mediatek_wireless
amd_gpu
intel_gpu
nvidia_gpu
bluetooth
```

## Safety / Operational Behavior

- Package operations use `apt-get` without shell interpolation.
- Repository files are backed up as `*.kalidriver.bak` before modification.
- `--dry-run` does not install packages or modify repository files.
- APT failures show diagnostic output and are written to the application log.
- Clearing the terminal only removes visible terminal output; it does **not** delete shell history or files.

## Project Structure

```text
kaliDriver/
├── kaliDriver.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

## Author

**Mohanad Sayed**

GitHub: https://github.com/MohanadSayed7/kaliDriver

## License

MIT
