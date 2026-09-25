#!/usr/bin/env python3
"""kaliDriver - Professional hardware, driver and firmware assistant for Kali Linux."""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

APP_NAME = "kaliDriver"
VERSION = "2.4.1"
LOG_FILE = Path.home() / ".kalidriver.log" if os.geteuid() != 0 else Path("/var/log/kalidriver.log")

console = Console()


@dataclass(frozen=True)
class DriverProfile:
    key: str
    name: str
    category: str
    description: str
    packages: tuple[str, ...]
    kernel_headers: bool = False


@dataclass
class HardwareDevice:
    bus: str
    description: str
    vendor: str = "Unknown"
    driver: str = "Unknown"
    driver_modules: list[str] = field(default_factory=list)
    device_id: str = ""


LOGO = r"""
▐▀▀▀▀█     █▀▀▀▀█     ▄▄███▄▄     ▐▀▀▀▀█        ▀▀▀▀▀▀▀▀    ▀▀▀▀▀▀▀▀▀▀▀▀     ▐▀▀▀▀▀▀▀▀▀█▄▄   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀      █▀▀▀▀█▐▀▀▀▀▀▀▀▀▀▀▀▀█▐▀▀▀▀▀▀▀▀▀█▄▄   
▐ ████     █ ████   ▄█▀▄▄▄▄▄██▄   ▐ ████        ▀▀▀▀▀▀▀▀    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  ▐ ████████████▄ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀      ██████▐ ████████████▐ ████████████▄ 
▐ ████     █ ████  █▀▄██████████  ▐ ████        ▀▀▀▀▀▀▀▀    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀█▀████▌▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀      ██████▐ ████▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀█▀████▌
▐ ████▄▄▄▄█▀▄███▌ ▐▌▐███████████▌ ▐ ████         █▀▀▀▀█     ▐▀▀▀▀█ ▀ ▀█▀▀▀▀▀▌▐ █ █ ▄▄▄█ ████▌ █▀▀▀▀█ ▐▀▀▀▀▀█      ██████▐ ████▄▄▄▄▄▄▄▄▐ █ █ ▄▄▄█ ████▌
▐ █████▄▄▄▄████▀  █ ████▀  ▀▀▀▀▀▀ ▐ ████         █ ████     ▐█████    ██████▌▐ █ █ ██▄▄████▀  █ ████ ▐ █████      █ ████▐ ████▄▄▄▄▄▄▄█▐ █ █ ██▄▄████▀ 
▐ ████████████ ▄▀▐▌▐███▌ ▀▀▀▀▀▀▀▀ ▐ ████         █ ████     ▐█████    ██████▌▐ █ █ ██████▀    █ ████ ▐▄▀████▌    ▐█ ████▐ ████████████▐ █ █ ██████▀   
▐▄████ ▄ ▀▀████▄ █ ████ ▀▀▀▀▀▀▀▀▀▀▐▄████         █ ████     ▐█████   ▄██████▌▐ █ █ ▀█▄▀███▄   █ ████  █▄▀████    ██████▌▐▄████        ▐ █ █ ▀█▄▀███▄  
▄▄▄▄▄▄  ▀▄  ██████ ████ ▀▀▀▀▀▀▀▀▀▀▄▄▄▄▄▄▄▄▄▄▄▄▄▄ █ ████     ▐█████▀▀▀▀▄█████ ▐ █ █ ▄ ▀█ ███▄  █ ████   █▄▀████▄▄█▀▄████ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▐ █ █ ▄ ▀█ ███▄ 
▄▄▄▄▄▄   █ ▄▄▄▄▄▄█ ████ ▀▀▀ █▀████▄▄▄▄▄▄▄▄▄▄▄▄▄▄ █ ████     ▐█████████████▀  ▐ █ █  ▀▄▐█ ████ █ ████  ▄ ▀█▄▀███▄▄████▀ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▐ █ █  ▀▄▐█ ████
▄▄▄▄▄▄   █ ▄▄▄▄▄▄█▄████     █▄████▄▄▄▄▄▄▄▄▄▄▄▄▄▄ █▄████     ▐▄▄████████▀▀ ▄▀ ▐ █ █   █ █▄████ █▄████   ▀▄ ▀▀██████▀▀ ▄▀ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▐ █ █   █ █▄████
▄▄▄▄▄▄   █▄▄▄▄▄▄▄▄▄▄▄▄▄     ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄     ▄▄▄▄▄▄▄▄▄▄▄▄▀▀   ▄ ▄ ▄   ▀▄▄▄▄▄▄▄ ▄▄▄▄▄▄     ▀▀▄▄▄▄▄▄▄▄▀▀   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ▄ ▄   ▀▄▄▄▄▄▄▄
"""


# These are package hints, not an exhaustive hardware whitelist.
DRIVER_PROFILES = {
    "wireless_common": DriverProfile(
        "wireless_common",
        "Common Wireless Firmware",
        "Wireless",
        "Install a broad set of Kali wireless firmware packages.",
        (
            "kali-linux-firmware",
            "firmware-iwlwifi",
            "firmware-realtek",
            "firmware-atheros",
            "firmware-brcm80211",
            "firmware-mediatek",
        ),
    ),
    "intel_wireless": DriverProfile(
        "intel_wireless", "Intel Wireless Firmware", "Wireless", "Intel Wi-Fi firmware support.", ("firmware-iwlwifi",)
    ),
    "realtek_wireless": DriverProfile(
        "realtek_wireless", "Realtek Wireless Firmware", "Wireless", "Realtek Wi-Fi firmware support.", ("firmware-realtek",)
    ),
    "atheros_wireless": DriverProfile(
        "atheros_wireless", "Atheros Wireless Firmware", "Wireless", "Atheros/Qualcomm wireless firmware support.", ("firmware-atheros",)
    ),
    "broadcom_wireless": DriverProfile(
        "broadcom_wireless", "Broadcom Wireless Firmware", "Wireless", "Broadcom wireless firmware support.", ("firmware-brcm80211",)
    ),
    "mediatek_wireless": DriverProfile(
        "mediatek_wireless", "MediaTek Wireless Firmware", "Wireless", "MediaTek wireless firmware support.", ("firmware-mediatek",)
    ),
    "amd_gpu": DriverProfile(
        "amd_gpu", "AMD GPU Stack", "Graphics", "Install Mesa/Vulkan components for AMD graphics.", ("mesa-vulkan-drivers", "firmware-amd-graphics"), True
    ),
    "intel_gpu": DriverProfile(
        "intel_gpu", "Intel GPU Stack", "Graphics", "Install Mesa/Vulkan components for Intel graphics.", ("mesa-vulkan-drivers", "intel-media-va-driver-non-free"), False
    ),
    "nvidia_gpu": DriverProfile(
        "nvidia_gpu", "NVIDIA GPU Driver", "Graphics", "Install NVIDIA proprietary driver and matching kernel headers.", ("nvidia-driver",), True
    ),
    "bluetooth": DriverProfile(
        "bluetooth", "Bluetooth Firmware", "Bluetooth", "Install common Bluetooth/Wi-Fi firmware families.", ("bluez", "kali-linux-firmware",)
    ),
}


def log_message(level: str, message: str) -> None:
    styles = {"INFO": "blue", "SUCCESS": "green", "ERROR": "red", "WARNING": "yellow"}
    style = styles.get(level, "white")
    console.print(f"[{style}][{level}][/{style}] {message}")
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")
    except OSError:
        pass


def log_info(message: str) -> None:
    log_message("INFO", message)


def log_success(message: str) -> None:
    log_message("SUCCESS", message)


def log_error(message: str) -> None:
    log_message("ERROR", message)


def log_warning(message: str) -> None:
    log_message("WARNING", message)


def clear_screen() -> None:
    """Hard-reset the visible terminal before rendering a new kaliDriver screen.

    This intentionally clears both the current screen and terminal scrollback.
    Kali users commonly run the tool from XFCE Terminal, where CSI 3 J is
    supported. The full-reset sequence is used as a fallback for terminals
    that do not fully honor the scrollback erase sequence. This does not
    delete shell history or files.
    """
    sequences = (
        "\x1b[3J\x1b[2J\x1b[1;1H",  # erase scrollback + screen + home
        "\x1b[H\x1b[2J\x1b[3J",      # alternate ordering for compatibility
    )
    try:
        for sequence in sequences:
            sys.stdout.write(sequence)
            sys.stdout.flush()
        # Rich keeps its own cursor/terminal state; refresh it without printing.
        console.clear(home=True)
    except Exception:
        # Last-resort visual clear for unusual/non-interactive terminals.
        console.print("\n" * 80, end="")


def clear_terminal_startup() -> None:
    """Clear the terminal aggressively once at startup, including scrollback."""
    if not sys.stdout.isatty():
        return
    try:
        # DEC private mode reset + scrollback erase + screen erase.
        sys.stdout.write("\x1b[?1049l\x1b[3J\x1b[2J\x1b[H")
        sys.stdout.flush()
    except OSError:
        pass
    clear_screen()


def print_banner() -> None:
    logo_text = Text(LOGO, style="bold green", no_wrap=True, overflow="crop", justify="center")
    version = Text(f"kaliDriver  •  v{VERSION}  •  Hardware / Driver / APT", style="bold white", justify="center")
    author = Text("Developed by Mohanad Sayed", style="green", justify="center")
    github = Text("github.com/MohanadSayed7/kaliDriver", style="bright_blue", justify="center")

    content = Group(logo_text, Text(""), version, author, github)
    console.print(Panel(
        content,
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2),
        expand=True,
    ))


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def is_root() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def run_command(command: Sequence[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(list(command), 127, "", f"Command not found: {command[0]}")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(list(command), 124, "", f"Command timed out: {' '.join(command)}")


def parse_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def check_platform() -> bool:
    os_info = parse_os_release()
    distro_id = os_info.get("ID", "unknown")
    if distro_id.lower() == "kali":
        log_success(f"Kali Linux detected ({os_info.get('VERSION_ID', 'rolling')}).")
        return True
    log_warning(f"Detected OS: {distro_id}. kaliDriver is designed for Kali Linux.")
    return False


def get_kernel_version() -> str:
    return platform.release()


def module_loaded(name: str) -> bool:
    result = run_command(["lsmod"])
    return result.returncode == 0 and any(line.split()[0] == name for line in result.stdout.splitlines()[1:] if line.split())


def vendor_from_pci_id(device_id: str) -> str:
    """Map common PCI vendor IDs without misclassifying subsystem text."""
    mapping = {
        "8086": "Intel",
        "1002": "AMD",
        "10de": "NVIDIA",
        "10ec": "Realtek",
        "14e4": "Broadcom",
        "168c": "Qualcomm/Atheros",
        "14c3": "MediaTek",
        "1814": "Ralink",
    }
    return mapping.get(device_id.split(":", 1)[0].lower(), "Unknown")


def scan_hardware() -> list[HardwareDevice]:
    devices: list[HardwareDevice] = []

    if command_exists("lspci"):
        pci = run_command(["lspci", "-nnk"])
        current: HardwareDevice | None = None
        for line in pci.stdout.splitlines():
            if line and not line.startswith((" ", "\t")):
                current = HardwareDevice(bus="PCI", description=line.strip())
                id_match = re.search(r"\[([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\]", line)
                if id_match:
                    current.device_id = id_match.group(1)
                if current.device_id:
                    current.vendor = vendor_from_pci_id(current.device_id)
                if current.vendor == "Unknown":
                    upper = line.upper()
                    if "NVIDIA" in upper:
                        current.vendor = "NVIDIA"
                    elif "REALTEK" in upper:
                        current.vendor = "Realtek"
                    elif "BROADCOM" in upper:
                        current.vendor = "Broadcom"
                    elif "QUALCOMM" in upper or "ATHEROS" in upper:
                        current.vendor = "Qualcomm/Atheros"
                    elif "MEDIATEK" in upper or "RALINK" in upper:
                        current.vendor = "MediaTek"
                devices.append(current)
            elif current is not None and "Kernel driver in use:" in line:
                current.driver = line.split(":", 1)[1].strip()
            elif current is not None and "Kernel modules:" in line:
                current.driver_modules = [x.strip() for x in line.split(":", 1)[1].split(",")]

    if command_exists("lsusb"):
        usb = run_command(["lsusb"])
        for line in usb.stdout.splitlines():
            if not line.strip():
                continue
            device = HardwareDevice(bus="USB", description=line.strip())
            match = re.search(r"ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})", line)
            if match:
                device.device_id = f"{match.group(1)}:{match.group(2)}"
            upper = line.upper()
            if "REALTEK" in upper:
                device.vendor = "Realtek"
            elif "INTEL" in upper:
                device.vendor = "Intel"
            elif "BROADCOM" in upper:
                device.vendor = "Broadcom"
            elif "QUALCOMM" in upper or "ATHEROS" in upper:
                device.vendor = "Qualcomm/Atheros"
            elif "MEDIATEK" in upper or "RALINK" in upper:
                device.vendor = "MediaTek"
            devices.append(device)

    return devices



def scan_network_interfaces() -> list[tuple[str, str]]:
    """Return network interfaces and their administrative/link state."""
    if not command_exists("ip"):
        return []
    result = run_command(["ip", "-br", "link"], timeout=30)
    rows: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
    return rows


def scan_storage_devices() -> list[tuple[str, str, str, str]]:
    """Return block device name, model, size and type when lsblk is available."""
    if not command_exists("lsblk"):
        return []
    result = run_command(["lsblk", "-dn", "-o", "NAME,MODEL,SIZE,TYPE"], timeout=30)
    rows: list[tuple[str, str, str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) >= 4:
            rows.append((parts[0], parts[1], parts[2], parts[3]))
        elif parts:
            rows.append((parts[0], "-", "-", parts[-1]))
    return rows


def show_network_and_storage() -> None:
    network = scan_network_interfaces()
    net_table = Table(title="Network Interfaces", box=box.ROUNDED, expand=True)
    net_table.add_column("Interface", style="cyan")
    net_table.add_column("State", style="green")
    if network:
        for name, state in network:
            net_table.add_row(name, state)
    else:
        net_table.add_row("-", "ip command unavailable or no interfaces returned")
    console.print(net_table)

    storage = scan_storage_devices()
    disk_table = Table(title="Storage Devices", box=box.ROUNDED, expand=True)
    disk_table.add_column("Name", style="cyan")
    disk_table.add_column("Model", style="white")
    disk_table.add_column("Size", style="green")
    disk_table.add_column("Type", style="magenta")
    if storage:
        for row in storage:
            disk_table.add_row(*row)
    else:
        disk_table.add_row("-", "No storage records", "-", "-")
    console.print(disk_table)

def build_hardware_table(devices: Sequence[HardwareDevice]) -> Table:
    table = Table(title="Hardware Inventory", box=box.ROUNDED, expand=True)
    table.add_column("Bus", style="bold cyan", width=6)
    table.add_column("Device", style="white", min_width=28)
    table.add_column("Vendor", style="magenta", width=16)
    table.add_column("Kernel Driver", style="green", width=20)
    table.add_column("Device ID", style="dim", width=12)
    if not devices:
        table.add_row("-", "No devices detected", "-", "-", "-")
        return table
    for device in devices:
        table.add_row(
            device.bus,
            device.description,
            device.vendor,
            device.driver,
            device.device_id or "-",
        )
    return table


def summarize_hardware(devices: Sequence[HardwareDevice]) -> None:
    counts: dict[str, int] = {}
    missing = 0
    for device in devices:
        counts[device.bus] = counts.get(device.bus, 0) + 1
        if device.bus == "PCI" and device.driver == "Unknown":
            missing += 1
    summary = "  ".join(f"{key}: {value}" for key, value in sorted(counts.items())) or "No hardware records"
    console.print(Panel(f"{summary}\nPCI devices without a reported active driver: {missing}", title="Scan Summary", border_style="blue"))


def find_vendors(devices: Iterable[HardwareDevice]) -> set[str]:
    return {d.vendor.lower() for d in devices if d.vendor and d.vendor != "Unknown"}


def suggest_profiles(devices: Sequence[HardwareDevice]) -> list[str]:
    vendors = find_vendors(devices)
    text = " ".join(d.description.lower() for d in devices)
    suggestions: list[str] = []
    if "nvidia" in vendors or "nvidia" in text:
        suggestions.append("nvidia_gpu")
    if "amd" in vendors or "ati" in text:
        suggestions.append("amd_gpu")
    if "intel" in vendors and any(token in text for token in ("vga", "3d", "display")):
        suggestions.append("intel_gpu")
    if "intel" in vendors and any(token in text for token in ("wireless", "wi-fi", "network")):
        suggestions.append("intel_wireless")
    if "realtek" in vendors:
        suggestions.append("realtek_wireless")
    if "broadcom" in vendors:
        suggestions.append("broadcom_wireless")
    if "qualcomm/atheros" in vendors:
        suggestions.append("atheros_wireless")
    if "mediatek" in vendors:
        suggestions.append("mediatek_wireless")
    if "bluetooth" in text:
        suggestions.append("bluetooth")
    return list(dict.fromkeys(suggestions))


def package_installed(package: str) -> bool:
    if not command_exists("dpkg-query"):
        return False
    result = run_command(["dpkg-query", "-W", "-f=${Status}", package])
    return result.returncode == 0 and "install ok installed" in result.stdout


def get_missing_packages(packages: Iterable[str]) -> list[str]:
    return [package for package in dict.fromkeys(packages) if not package_installed(package)]


def source_files() -> tuple[Path, Path]:
    return Path("/etc/apt/sources.list.d/kali.sources"), Path("/etc/apt/sources.list")


def source_has_required_components(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    required = {"main", "contrib", "non-free", "non-free-firmware"}
    for line in text.splitlines():
        if re.match(r"^\s*Components:\s*", line):
            components = set(line.split(":", 1)[1].split())
            if required.issubset(components):
                return True
        elif re.match(r"^\s*deb\s+", line) and "http.kali.org/kali" in line:
            components = set(line.split()[3:])
            if required.issubset(components):
                return True
    return False


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(path.name + ".kalidriver.bak")
    shutil.copy2(path, backup)
    return backup


def ensure_kali_repositories() -> bool:
    modern, legacy = source_files()
    if source_has_required_components(modern) or source_has_required_components(legacy):
        log_success("Kali repositories already expose main, contrib, non-free and non-free-firmware.")
        return True

    try:
        if modern.exists():
            backup = backup_file(modern)
            original = modern.read_text(encoding="utf-8", errors="replace").splitlines()
            updated: list[str] = []
            changed = False
            for line in original:
                if re.match(r"^\s*Components:\s*", line):
                    updated.append("Components: main contrib non-free non-free-firmware")
                    changed = True
                else:
                    updated.append(line)
            if not changed:
                updated.extend(
                    [
                        "",
                        "Types: deb",
                        "URIs: http://http.kali.org/kali/",
                        "Suites: kali-rolling",
                        "Components: main contrib non-free non-free-firmware",
                        "Signed-By: /usr/share/keyrings/kali-archive-keyring.gpg",
                    ]
                )
            modern.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
            log_success(f"Updated {modern}. Backup: {backup}")
            return True

        backup = backup_file(legacy)
        content = legacy.read_text(encoding="utf-8", errors="replace") if legacy.exists() else ""
        lines = content.splitlines()
        updated = []
        changed = False
        for line in lines:
            if re.match(r"^\s*deb\s+", line) and "http.kali.org/kali" in line:
                parts = line.split()
                components = parts[3:]
                required = ["main", "contrib", "non-free", "non-free-firmware"]
                for item in required:
                    if item not in components:
                        components.append(item)
                updated.append(" ".join(parts[:3] + components))
                changed = True
            else:
                updated.append(line)
        if not changed:
            updated.append("deb http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware")
        legacy.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
        log_success(f"Updated {legacy}. Backup: {backup}")
        return True
    except OSError as exc:
        log_error(f"Unable to modify APT repository configuration: {exc}")
        return False


def apt_update(*, dry_run: bool = False) -> bool:
    if not command_exists("apt-get"):
        log_error("apt-get is unavailable.")
        return False
    if dry_run:
        log_info("Dry-run mode: would run `apt-get update`.")
        return True

    with console.status("[blue]Refreshing APT metadata...[/blue]", spinner="dots"):
        result = run_command(["apt-get", "update"], timeout=300)
    if result.returncode != 0:
        tail = "\n".join((result.stderr or result.stdout).splitlines()[-12:])
        log_error("APT update failed.")
        console.print(Panel(tail or "No APT diagnostic output.", title="APT Diagnostics", border_style="red"))
        return False
    log_success("APT metadata refreshed successfully.")
    return True


def apt_upgrade(*, full: bool = False, dry_run: bool = False) -> bool:
    """Upgrade installed packages through APT.

    By default this uses `apt-get upgrade`; `full=True` uses `full-upgrade`
    when the user explicitly requests the more comprehensive mode.
    """
    if not command_exists("apt-get"):
        log_error("apt-get is unavailable.")
        return False

    action = "full-upgrade" if full else "upgrade"
    label = "full system upgrade" if full else "system upgrade"
    command = ["apt-get", action, "-y"]

    if dry_run:
        log_info(f"Dry-run mode: would run `apt-get {action} -y`.")
        return True

    with console.status(f"[blue]Running {label}...[/blue]", spinner="dots"):
        result = run_command(command, timeout=3600)

    if result.returncode != 0:
        tail = "\n".join((result.stderr or result.stdout).splitlines()[-16:])
        log_error(f"APT {action} failed.")
        console.print(Panel(tail or "No APT diagnostic output.", title="APT Diagnostics", border_style="red"))
        return False

    log_success(f"APT {label} completed successfully.")
    return True


def apt_update_and_upgrade(*, full: bool = False, dry_run: bool = False) -> bool:
    """Refresh package metadata, then upgrade installed packages."""
    log_info("Starting system update and upgrade sequence.")
    if dry_run:
        log_info("Dry-run mode: repository files will not be changed.")
    elif not ensure_kali_repositories():
        return False
    if not apt_update(dry_run=dry_run):
        return False
    return apt_upgrade(full=full, dry_run=dry_run)


def apt_install(packages: Sequence[str], *, dry_run: bool = False) -> bool:
    missing = get_missing_packages(packages)
    if not missing:
        log_success("All requested packages are already installed.")
        return True

    console.print(Panel("\n".join(f"• {pkg}" for pkg in missing), title="Installation Plan", border_style="blue"))
    if dry_run:
        log_info("Dry-run mode: no packages were installed.")
        return True

    failed: list[str] = []
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    )
    with progress:
        task = progress.add_task("Installing packages", total=len(missing))
        for package in missing:
            progress.update(task, description=f"Installing {package}")
            result = run_command(["apt-get", "install", "-y", package], timeout=600)
            if result.returncode == 0:
                log_success(f"Installed {package}.")
            else:
                failed.append(package)
                error_tail = (result.stderr or result.stdout).splitlines()[-1:] or ["Unknown APT error"]
                log_error(f"Failed to install {package}: {error_tail[0]}")
            progress.advance(task)

    if failed:
        log_error("Failed packages: " + ", ".join(failed))
        return False
    log_success("Installation completed successfully.")
    return True


def kernel_headers_package() -> str | None:
    kernel = get_kernel_version()
    if re.fullmatch(r"[A-Za-z0-9._+:-]+", kernel):
        return f"linux-headers-{kernel}"
    return None


def install_profile(profile_key: str, *, dry_run: bool = False) -> bool:
    profile = DRIVER_PROFILES.get(profile_key)
    if profile is None:
        log_error(f"Unknown profile: {profile_key}")
        return False
    if not ensure_kali_repositories():
        return False
    if not apt_update(dry_run=dry_run):
        return False

    packages = list(profile.packages)
    if profile.kernel_headers:
        headers = kernel_headers_package()
        if headers:
            packages.insert(0, headers)
        else:
            log_warning("Could not derive a safe matching kernel headers package.")
    packages.extend(["dkms", "pciutils", "usbutils"])
    return apt_install(packages, dry_run=dry_run)


def show_repo_status() -> None:
    modern, legacy = source_files()
    table = Table(title="APT Repository Status", box=box.ROUNDED)
    table.add_column("File", style="cyan")
    table.add_column("Exists", style="white")
    table.add_column("Required Components", style="green")
    for path in (modern, legacy):
        table.add_row(str(path), "Yes" if path.exists() else "No", "OK" if source_has_required_components(path) else "Missing")
    console.print(table)


def show_driver_menu() -> str | None:
    profiles = list(DRIVER_PROFILES.values())
    table = Table(title="Driver & Firmware Profiles", box=box.ROUNDED, expand=True)
    table.add_column("#", width=4, style="bold cyan")
    table.add_column("Category", width=12, style="magenta")
    table.add_column("Profile", width=28, style="bold white")
    table.add_column("Purpose", style="dim")
    for index, profile in enumerate(profiles, 1):
        table.add_row(str(index), profile.category, profile.name, profile.description)
    console.print(table)
    choice = console.input("[bold cyan]Select a profile (Q to cancel): [/bold cyan]").strip()
    if choice.lower() == "q":
        return None
    if not choice.isdigit() or not 1 <= int(choice) <= len(profiles):
        log_error("Invalid selection.")
        return None
    return profiles[int(choice) - 1].key


def show_system_info() -> None:
    os_info = parse_os_release()
    table = Table(title="System Information", box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="white")
    rows = [
        ("Distribution", os_info.get("PRETTY_NAME", "Unknown")),
        ("Kernel", get_kernel_version()),
        ("Architecture", platform.machine()),
        ("Python", platform.python_version()),
        ("Root", "Yes" if is_root() else "No"),
        ("APT", "Available" if command_exists("apt-get") else "Missing"),
        ("PCI scanner", "Available" if command_exists("lspci") else "Missing"),
        ("USB scanner", "Available" if command_exists("lsusb") else "Missing"),
        ("Log file", str(LOG_FILE)),
    ]
    for key, value in rows:
        table.add_row(key, value)
    console.print(table)


def full_diagnostic(*, dry_run: bool = False) -> list[HardwareDevice]:
    with console.status("[blue]Running full hardware diagnostic...[/blue]", spinner="dots"):
        devices = scan_hardware()
    console.print(build_hardware_table(devices))
    summarize_hardware(devices)
    suggestions = suggest_profiles(devices)
    if suggestions:
        console.print(Rule("Recommended Profiles"))
        for key in suggestions:
            profile = DRIVER_PROFILES[key]
            console.print(f"[cyan]•[/cyan] {profile.name} — {profile.description}")
        if dry_run:
            log_info("Dry-run is enabled; recommendations are informational only.")
    else:
        log_info("No specialized profile matched. Use the device inventory and kernel driver fields for manual diagnosis.")
    return devices


def startup_workflow(*, full_upgrade: bool = False, dry_run: bool = False) -> int:
    """Run the default one-command maintenance workflow before opening the menu."""
    console.print(Rule("Automatic Startup Maintenance"))
    log_info("Default mode runs repository checks, APT update, package upgrade, and hardware discovery.")

    if not apt_update_and_upgrade(full=full_upgrade, dry_run=dry_run):
        log_warning("System maintenance finished with errors. Continuing to hardware diagnostics.")

    devices = full_diagnostic(dry_run=dry_run)
    suggestions = suggest_profiles(devices)
    if suggestions:
        console.print(Panel(
            "\n".join(f"• {DRIVER_PROFILES[key].name}" for key in suggestions),
            title="Recommended Driver Actions",
            border_style="cyan",
        ))
        log_info("Open the driver menu to apply a recommended profile. No driver is installed automatically without a user selection.")
    return 0


def pause_before_menu() -> None:
    console.input("\n[dim]Press Enter to return to the main menu...[/dim]")
    clear_screen()
    print_banner()


def show_maintenance_menu(*, dry_run: bool = False) -> None:
    while True:
        menu = Table(title="System Maintenance", box=box.ROUNDED, show_header=False, expand=True)
        menu.add_row("1", "APT repository status")
        menu.add_row("2", "Repair / enable Kali firmware repositories")
        menu.add_row("3", "Update APT metadata")
        menu.add_row("4", "Upgrade installed packages")
        menu.add_row("5", "Update + Upgrade system")
        menu.add_row("0", "Back to main menu")
        console.print(menu)
        choice = console.input("[bold cyan]Select an option [0-5]: [/bold cyan]").strip().lower()
        if choice == "1":
            show_repo_status()
            pause_before_menu()
        elif choice == "2":
            ensure_kali_repositories()
            pause_before_menu()
        elif choice == "3":
            apt_update(dry_run=dry_run)
            pause_before_menu()
        elif choice == "4":
            apt_upgrade(dry_run=dry_run)
            pause_before_menu()
        elif choice == "5":
            apt_update_and_upgrade(dry_run=dry_run)
            pause_before_menu()
        elif choice in {"0", "q", "back"}:
            return
        else:
            log_error("Unknown maintenance option.")


def menu_loop(*, dry_run: bool = False) -> int:
    while True:
        menu = Table(title="Main Menu", box=box.ROUNDED, show_header=False, expand=True)
        menu.add_row("1", "Hardware Diagnostics", "Full hardware + network + storage scan")
        menu.add_row("2", "System Maintenance", "Repositories, Update, Upgrade")
        menu.add_row("3", "Driver & Firmware Manager", "Install a recommended driver profile")
        menu.add_row("4", "System Information", "Kali, kernel, Python and tool status")
        menu.add_row("0", "Exit", "Close kaliDriver")
        console.print(menu)
        choice = console.input("[bold cyan]Select an option [0-4]: [/bold cyan]").strip().lower()

        if choice == "1":
            full_diagnostic(dry_run=dry_run)
            show_network_and_storage()
            pause_before_menu()
        elif choice == "2":
            clear_screen()
            print_banner()
            show_maintenance_menu(dry_run=dry_run)
            clear_screen()
            print_banner()
        elif choice == "3":
            profile = show_driver_menu()
            if profile:
                install_profile(profile, dry_run=dry_run)
            pause_before_menu()
        elif choice == "4":
            show_system_info()
            pause_before_menu()
        elif choice in {"0", "q", "quit", "exit"}:
            log_info("Exiting kaliDriver.")
            return 0
        else:
            log_error("Unknown menu option. Please choose 0-4.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Professional Kali Linux hardware, driver and firmware assistant.",
    )
    parser.add_argument("--scan", action="store_true", help="Run a hardware scan and exit.")
    parser.add_argument("--diagnose", action="store_true", help="Run a full diagnostic and exit.")
    parser.add_argument("--install", metavar="PROFILE", help="Install a named driver profile.")
    parser.add_argument("--repo-check", action="store_true", help="Display APT repository status and exit.")
    parser.add_argument("--repo-fix", action="store_true", help="Enable the standard Kali firmware repository components.")
    parser.add_argument("--update", action="store_true", help="Run apt update and exit.")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade installed packages and exit.")
    parser.add_argument("--update-upgrade", action="store_true", help="Run update followed by package upgrade and exit.")
    parser.add_argument("--full-upgrade", action="store_true", help="Use apt full-upgrade instead of apt upgrade.")
    parser.add_argument("--dry-run", action="store_true", help="Show plans without installing packages.")
    parser.add_argument("--skip-maintenance", action="store_true", help="Skip the automatic update/upgrade workflow at startup.")
    return parser.parse_args()


def relaunch_as_root() -> int | None:
    """Re-launch the same Python interpreter through sudo when needed."""
    if is_root():
        return None
    sudo = shutil.which("sudo")
    if not sudo:
        log_error("Root privileges are required, but sudo is not available.")
        log_info(f"Run manually with: sudo {sys.executable} {Path(__file__).name}")
        return 1

    log_info("Root privileges are required. Requesting sudo access...")
    script = str(Path(__file__).resolve())
    try:
        os.execv(sudo, [sudo, sys.executable, script, *sys.argv[1:]])
    except OSError as exc:
        log_error(f"Unable to re-launch with sudo: {exc}")
        return 1
    return 1

def main() -> int:
    args = parse_args()
    clear_terminal_startup()

    elevated = relaunch_as_root()
    if elevated is not None:
        return elevated

    print_banner()
    check_platform()
    log_info(f"Kernel: {get_kernel_version()} | Architecture: {platform.machine()}")

    if args.scan:
        devices = scan_hardware()
        console.print(build_hardware_table(devices))
        summarize_hardware(devices)
        return 0
    if args.diagnose:
        full_diagnostic(dry_run=args.dry_run)
        return 0
    if args.repo_check:
        show_repo_status()
        return 0
    if args.repo_fix:
        return 0 if ensure_kali_repositories() else 1
    if args.update:
        return 0 if apt_update(dry_run=args.dry_run) else 1
    if args.upgrade:
        return 0 if apt_upgrade(full=args.full_upgrade, dry_run=args.dry_run) else 1
    if args.update_upgrade:
        return 0 if apt_update_and_upgrade(full=args.full_upgrade, dry_run=args.dry_run) else 1
    if args.install:
        return 0 if install_profile(args.install, dry_run=args.dry_run) else 1

    if not args.skip_maintenance:
        startup_workflow(full_upgrade=args.full_upgrade, dry_run=args.dry_run)

    return menu_loop(dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        raise SystemExit(130)
