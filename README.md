# kaliDriver

`kaliDriver` is a professional, English-language CLI assistant for Kali Linux that inventories hardware, exposes kernel driver information, validates Kali APT firmware components, and installs common driver/firmware profiles.

## What is new in v2.2

- Randomized startup ASCII identity: a different banner is selected on every launch.
- Full PCI inventory using `lspci -nnk`, including the active kernel driver and available kernel modules when reported.
- USB inventory using `lsusb`.
- Network interface inventory using `ip -br link`.
- Storage inventory using `lsblk`.
- Vendor-aware recommendations for Intel, AMD, NVIDIA, Realtek, Broadcom, Qualcomm/Atheros and MediaTek hardware.
- Generic Linux hardware support: devices are not limited to a fixed model list; anything visible through PCI/USB tooling can be inventoried.
- APT repository validation and repair for Kali's modern `kali.sources` and legacy `sources.list` layouts.
- Progress bars, live status spinners, installation plans, diagnostic output, and persistent logs.
- Easy Mode startup: plain `sudo ./kaliDriver.py` automatically runs repository maintenance, `apt update`, package upgrade, and a full hardware diagnostic before opening the menu.
- Command-line automation flags such as `--scan`, `--diagnose`, `--install`, `--repo-check`, `--repo-fix`, `--update`, `--upgrade`, `--update-upgrade`, `--full-upgrade`, and `--dry-run`.
- Automatic backups before editing repository configuration.
- NVIDIA/AMD profiles can add matching kernel headers where appropriate.

## Important scope

No Linux utility can guarantee support for literally every physical device. `kaliDriver` is designed to **discover any hardware the Linux system exposes through standard PCI/USB tools**, show the current kernel driver, and then provide package-level remediation for common vendor families. Unsupported or unusual hardware is presented for manual diagnosis rather than receiving a made-up driver package.

## Requirements

- Kali Linux
- Python 3.10+
- Root privileges for repository changes and package installation
- `apt-get`
- `pciutils` (`lspci`)
- `usbutils` (`lsusb`)
- Internet access for package installation
- `rich`

Install the Python dependency in a virtual environment if needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

Recommended Easy Mode:

```bash
sudo ./kaliDriver.py
```

The default launch automatically performs:

```text
1. Validate Kali + root access
2. Check/enable Kali firmware repositories
3. apt update
4. apt upgrade (or apt full-upgrade when selected explicitly)
5. Full PCI/USB/network/storage hardware diagnostic
6. Show driver recommendations
7. Open the interactive main menu
```

To open the menu without automatic update/upgrade:

```bash
sudo ./kaliDriver.py --skip-maintenance
```

After installation as a CLI command:

```bash
sudo kaliDriver
```

Command examples:

```bash
sudo kaliDriver --scan
sudo kaliDriver --diagnose
sudo kaliDriver --repo-check
sudo kaliDriver --repo-fix
sudo kaliDriver --install nvidia_gpu --dry-run
```

## Available install profiles

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

## Safety / operational behavior

- Package installation uses `apt-get` directly without shell execution.
- Repository files are backed up as `*.kalidriver.bak` before modification.
- `--dry-run` shows the package plan without installing packages.
- APT failures display diagnostic output and are logged.
- The application writes operational logs to `~/.kalidriver.log` when possible, or `/var/log/kalidriver.log` when running as root.

## Project layout

```text
kaliDriver/
├── kaliDriver.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## GitHub

Suggested repository name:

```text
kaliDriver
```

Suggested first commit:

```bash
git init
git add .
git commit -m "feat: add professional Kali Linux driver assistant v2"
```

## License

MIT

### System maintenance

The normal command already performs update + upgrade automatically. Use `--update`, `--upgrade`, or `--update-upgrade` for focused non-interactive maintenance; add `--full-upgrade` for the comprehensive APT upgrade mode.
