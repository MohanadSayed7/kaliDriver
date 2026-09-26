#!/usr/bin/env python3
"""kaliDriver v3 - automatic hardware, driver, firmware and system maintenance assistant."""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

try:
    from rich import box
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
    RICH = True
except ImportError:
    RICH = False

APP_NAME = "kaliDriver"
VERSION = "3.1.0"
LOG_FILE = Path("/var/log/kalidriver.log") if os.geteuid() == 0 else Path.home() / ".kalidriver.log"
console = Console() if RICH else None


@dataclass
class Device:
    bus: str
    address: str
    description: str
    device_id: str = ""
    vendor: str = "Unknown"
    driver: str = ""
    modules: list[str] = field(default_factory=list)
    class_name: str = ""

    @property
    def has_driver(self) -> bool:
        return bool(self.driver and self.driver.lower() not in {"none", "unknown", "n/a"})


@dataclass
class Repair:
    device: str
    device_id: str
    packages: list[str]
    module: str = ""
    reason: str = ""


@dataclass
class FirmwareIssue:
    raw: str
    firmware: str = ""
    subsystem: str = ""


def out(msg: str = "") -> None:
    if RICH:
        console.print(msg)
    else:
        print(msg)


def info(msg: str) -> None:
    out(f"[blue][INFO][/blue] {msg}" if RICH else f"[INFO] {msg}")
    log("INFO", msg)


def ok(msg: str) -> None:
    out(f"[green][OK][/green] {msg}" if RICH else f"[OK] {msg}")
    log("SUCCESS", msg)


def warn(msg: str) -> None:
    out(f"[yellow][WARN][/yellow] {msg}" if RICH else f"[WARN] {msg}")
    log("WARNING", msg)


def error(msg: str) -> None:
    out(f"[red][ERROR][/red] {msg}" if RICH else f"[ERROR] {msg}")
    log("ERROR", msg)


def log(level: str, msg: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}\n")
    except OSError:
        pass


def run(cmd: Sequence[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(list(cmd), text=True, capture_output=True, check=False, timeout=timeout)
    except FileNotFoundError:
        return subprocess.CompletedProcess(list(cmd), 127, "", f"Command not found: {cmd[0]}")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(list(cmd), 124, "", "Command timed out")


def exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


def banner() -> None:
    title = f"{APP_NAME}  v{VERSION}"
    sub = "Automatic Hardware • Driver • Firmware • Update & Upgrade"
    if RICH:
        console.print(Panel(Group(Text(title, style="bold cyan", justify="center"), Text(sub, style="white", justify="center")), border_style="cyan", box=box.DOUBLE, padding=(1, 2)))
    else:
        print(f"\n=== {title} ===\n{sub}\n")


def os_info() -> dict[str, str]:
    data: dict[str, str] = {}
    p = Path("/etc/os-release")
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                data[k] = v.strip().strip('"')
    return data


def ensure_kali() -> bool:
    ident = os_info().get("ID", "").lower()
    if ident != "kali":
        warn(f"Detected OS: {ident or 'unknown'}. This program is designed for Kali Linux.")
    else:
        ok(f"Kali Linux detected ({os_info().get('VERSION_ID', 'rolling')}).")
    return ident == "kali"


def apt_installed(pkg: str) -> bool:
    r = run(["dpkg-query", "-W", "-f=${Status}", pkg], 30)
    return r.returncode == 0 and "install ok installed" in r.stdout


def apt_candidate(pkg: str) -> bool:
    r = run(["apt-cache", "policy", pkg], 30)
    return r.returncode == 0 and bool(re.search(r"Candidate:\s+(?!\(none\))\S+", r.stdout))


def apt_update() -> bool:
    info("Refreshing APT package metadata...")
    r = run(["apt-get", "update"], 600)
    if r.returncode:
        error("APT update failed.")
        out((r.stderr or r.stdout)[-5000:])
        return False
    ok("APT metadata is up to date.")
    return True


def apt_upgrade() -> bool:
    info("Updating installed packages and system components...")
    r = run(["apt-get", "upgrade", "-y"], 1800)
    if r.returncode:
        error("APT upgrade failed.")
        out((r.stderr or r.stdout)[-5000:])
        return False
    ok("System upgrade completed.")
    return True


def install_packages(pkgs: list[str]) -> tuple[bool, list[str]]:
    unique = list(dict.fromkeys(p for p in pkgs if p))
    missing = [p for p in unique if not apt_installed(p)]
    if not missing:
        ok("All required packages are already installed.")
        return True, []

    unavailable = [p for p in missing if not apt_candidate(p)]
    if unavailable:
        warn("Unavailable packages in current APT sources: " + ", ".join(unavailable))
        missing = [p for p in missing if p not in unavailable]
    if not missing:
        return False, unavailable

    info("Installing required packages: " + ", ".join(missing))
    r = run(["apt-get", "install", "-y", *missing], 1800)
    if r.returncode:
        error("Package installation failed.")
        out((r.stderr or r.stdout)[-6000:])
        return False, missing
    ok("Required packages installed.")
    return True, []


def parse_pci() -> list[Device]:
    devices: list[Device] = []
    if not exists("lspci"):
        return devices
    r = run(["lspci", "-nnk"], 60)
    current: Device | None = None
    for line in r.stdout.splitlines():
        if line and not line[0].isspace():
            m_addr = re.match(r"([^ ]+)\s+(.*)", line)
            address = m_addr.group(1) if m_addr else ""
            desc = m_addr.group(2) if m_addr else line.strip()
            m_id = re.search(r"\[([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\]", line)
            did = m_id.group(1).lower() if m_id else ""
            upper = line.upper()
            vendor = next((v for key, v in [("NVIDIA", "NVIDIA"), ("AMD", "AMD"), ("ATI", "AMD"), ("INTEL", "Intel"), ("REALTEK", "Realtek"), ("BROADCOM", "Broadcom"), ("QUALCOMM", "Qualcomm/Atheros"), ("ATHEROS", "Qualcomm/Atheros"), ("MEDIATEK", "MediaTek"), ("Ralink".upper(), "MediaTek")] if key in upper), "Unknown")
            cls = "GPU" if any(x in upper for x in ("VGA", "3D CONTROLLER", "DISPLAY CONTROLLER")) else "Network" if any(x in upper for x in ("NETWORK CONTROLLER", "ETHERNET CONTROLLER")) else "Other"
            current = Device("PCI", address, desc, did, vendor, class_name=cls)
            devices.append(current)
        elif current:
            m = re.search(r"Kernel driver in use:\s*(\S+)", line)
            if m:
                current.driver = m.group(1)
            m = re.search(r"Kernel modules:\s*(.+)", line)
            if m:
                current.modules = [x.strip() for x in m.group(1).split(",")]
    return devices


def parse_usb() -> list[Device]:
    devices: list[Device] = []
    if not exists("lsusb"):
        return devices
    r = run(["lsusb"], 60)
    for line in r.stdout.splitlines():
        m = re.search(r"ID\s+([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s+(.+)$", line)
        if not m:
            continue
        did = m.group(1).lower()
        desc = m.group(2).strip()
        upper = desc.upper()
        vendor = next((v for key, v in [("REALTEK", "Realtek"), ("INTEL", "Intel"), ("BROADCOM", "Broadcom"), ("QUALCOMM", "Qualcomm/Atheros"), ("ATHEROS", "Qualcomm/Atheros"), ("MEDIATEK", "MediaTek"), ("RALINK", "MediaTek")] if key in upper), "Unknown")
        cls = "Bluetooth" if "BLUETOOTH" in upper else "USB Network" if any(x in upper for x in ("WIRELESS", "WLAN", "NETWORK")) else "USB"
        devices.append(Device("USB", "", desc, did, vendor, class_name=cls))
    return devices


def scan_hardware() -> list[Device]:
    devices = parse_pci() + parse_usb()
    # Add kernel-visible Bluetooth adapters/interfaces not always obvious in lsusb.
    if exists("rfkill"):
        r = run(["rfkill", "list"], 30)
        if "Bluetooth" in r.stdout and not any(d.class_name == "Bluetooth" for d in devices):
            devices.append(Device("Kernel", "hci0", "Bluetooth controller reported by rfkill", vendor="Broadcom", class_name="Bluetooth"))
    return devices


def firmware_issues() -> list[FirmwareIssue]:
    if not exists("dmesg"):
        return []
    r = run(["dmesg"], 60)
    text = r.stdout + "\n" + r.stderr
    issues: list[FirmwareIssue] = []
    patterns = [
        r"firmware: failed to load ['\"]?([^'\"\s]+)",
        r"Direct firmware load for\s+([^\s]+)\s+failed",
        r"Firmware.*?([A-Za-z0-9_.-]+\.bin).*?not found",
        r"BCM:\s+firmware Patch file not found",
    ]
    seen: set[str] = set()
    for line in text.splitlines():
        if not re.search(r"firmware|Patch file not found|not found", line, re.I):
            continue
        firmware = ""
        for pat in patterns:
            m = re.search(pat, line, re.I)
            if m:
                firmware = m.group(1) if m.groups() else "unknown"
                break
        key = line.strip()
        if key not in seen:
            seen.add(key)
            issues.append(FirmwareIssue(key, firmware))
    return issues


def exact_repairs(devices: list[Device]) -> list[Repair]:
    repairs: list[Repair] = []
    for d in devices:
        did = d.device_id.lower()
        desc = d.description.lower()
        if d.bus == "PCI" and did == "14e4:4365":
            if d.driver != "wl":
                repairs.append(Repair(d.description, did, ["broadcom-sta-dkms"], "wl", "Broadcom BCM43142 exact PCI ID"))
        elif d.bus == "PCI" and not d.has_driver:
            # Only map well-known classes/vendors when a safe package family is known.
            if d.vendor == "Intel" and "network" in desc:
                repairs.append(Repair(d.description, did, ["firmware-iwlwifi"], reason="Intel wireless firmware"))
            elif d.vendor == "Realtek" and "network" in desc:
                repairs.append(Repair(d.description, did, ["firmware-realtek"], reason="Realtek wireless firmware"))
            elif d.vendor == "MediaTek" and "network" in desc:
                repairs.append(Repair(d.description, did, ["firmware-mediatek"], reason="MediaTek wireless firmware"))
            elif d.vendor == "Qualcomm/Atheros" and "network" in desc:
                repairs.append(Repair(d.description, did, ["firmware-atheros"], reason="Atheros wireless firmware"))
    return repairs


def firmware_packages(devices: list[Device], issues: list[FirmwareIssue]) -> list[str]:
    pkgs: list[str] = []
    # These packages provide firmware collections; they are not claimed to contain every .hcd file.
    if any(i.firmware.lower().startswith("brcm/") for i in issues) or any(d.vendor == "Broadcom" and d.class_name == "Bluetooth" for d in devices):
        pkgs += ["kali-linux-firmware", "bluez"]
    if any(d.vendor == "Intel" and d.class_name in {"Network", "USB Network"} for d in devices):
        pkgs.append("firmware-iwlwifi")
    if any(d.vendor == "Realtek" and d.class_name in {"Network", "USB Network"} for d in devices):
        pkgs.append("firmware-realtek")
    if any(d.vendor == "MediaTek" and d.class_name in {"Network", "USB Network"} for d in devices):
        pkgs.append("firmware-mediatek")
    if any(d.vendor == "Qualcomm/Atheros" and d.class_name in {"Network", "USB Network"} for d in devices):
        pkgs.append("firmware-atheros")
    return list(dict.fromkeys(pkgs))


def load_module(module: str) -> bool:
    if not module or not exists("modprobe"):
        return False
    info(f"Loading kernel module: {module}")
    r = run(["modprobe", module], 60)
    if r.returncode:
        warn(f"Could not load {module}: {(r.stderr or r.stdout).strip()[-500:]}")
        return False
    return True


def verification(devices: list[Device], before: dict[str, str] | None = None) -> tuple[bool, list[Device]]:
    fresh = scan_hardware()
    problems: list[str] = []
    # Exact verification for Broadcom BCM43142.
    bcm = [d for d in fresh if d.device_id == "14e4:4365"]
    if bcm and bcm[0].driver != "wl":
        problems.append("Broadcom BCM43142 is not using wl")
    for d in fresh:
        if d.class_name in {"GPU", "Network", "Bluetooth"} and not d.has_driver:
            # Bluetooth may be represented by rfkill only, so don't fail solely on the synthetic entry.
            if d.class_name != "Bluetooth":
                problems.append(f"No active kernel driver: {d.description}")
    if problems:
        for p in problems:
            warn(p)
        return False, fresh
    ok("Hardware driver verification completed.")
    return True, fresh


def system_reboot_needed() -> bool:
    if Path("/var/run/reboot-required").exists():
        return True
    # Kernel package changes commonly create the marker; also detect installed kernel newer than running.
    if exists("dpkg-query"):
        r = run(["dpkg-query", "-W", "-f=${binary:Package} ${Version}\n"], 30)
        if "linux-image" in r.stdout and Path("/var/run/reboot-required.pkgs").exists():
            return True
    return False


def show_summary(devices: list[Device], issues: list[FirmwareIssue], repairs: list[Repair]) -> None:
    if RICH:
        table = Table(title="Hardware Status", box=box.ROUNDED, expand=True)
        table.add_column("Bus", width=7)
        table.add_column("Device")
        table.add_column("ID", width=12)
        table.add_column("Driver", width=18)
        table.add_column("Status", width=12)
        for d in devices:
            status = "OK" if d.has_driver else "NEEDS DRIVER"
            style = "green" if status == "OK" else "yellow"
            table.add_row(d.bus, d.description[:60], d.device_id or "-", d.driver or "none", f"[{style}]{status}[/{style}]")
        console.print(table)
    else:
        for d in devices:
            print(f"{d.bus:6} {d.device_id:12} {d.driver or 'none':18} {d.description}")
    info(f"Detected {len(devices)} hardware entries.")
    if repairs:
        warn(f"Driver repair candidates: {len(repairs)}")
    if issues:
        warn(f"Firmware diagnostic messages: {len(issues)}")


def full_run() -> int:
    if not root():
        error("Root privileges are required. Run: sudo python3 kaliDriver.py")
        return 1
    ensure_kali()
    if not exists("apt-get"):
        error("apt-get is unavailable.")
        return 1

    info("Step 1/7 — Scanning hardware and current drivers...")
    devices = scan_hardware()
    issues = firmware_issues()
    repairs = exact_repairs(devices)
    show_summary(devices, issues, repairs)

    info("Step 2/7 — Preparing Kali repositories and APT metadata...")
    if not apt_update():
        return 1

    info("Step 3/7 — Resolving exact driver/firmware requirements...")
    packages: list[str] = ["pciutils", "usbutils", "dkms", "linux-headers-" + platform.release(), "kali-linux-firmware"]
    modules: list[str] = []
    for repair in repairs:
        packages.extend(repair.packages)
        if repair.module:
            modules.append(repair.module)
    packages.extend(firmware_packages(devices, issues))
    # Remove a headers package if it isn't available; this should never make unrelated repairs fail.
    packages = list(dict.fromkeys(packages))
    packages = [p for p in packages if apt_candidate(p)]
    info("Resolved package plan: " + (", ".join(packages) if packages else "none"))

    info("Step 4/7 — Installing required drivers, firmware and support packages...")
    success, failed = install_packages(packages)
    if not success and failed:
        warn("Some packages could not be installed; continuing with verification where possible.")

    info("Step 5/7 — Loading newly installed kernel modules...")
    for module in dict.fromkeys(modules):
        load_module(module)

    # Give udev/kernel a moment to bind newly loaded drivers.
    time.sleep(2)
    info("Step 6/7 — Verifying hardware again...")
    verified, fresh = verification(devices)
    fresh_issues = firmware_issues()
    if fresh_issues:
        warn(f"Kernel still reports {len(fresh_issues)} firmware-related message(s). These are reported separately from driver status.")
        # Show only unique firmware names/lines to avoid pretending duplicate dmesg lines are distinct devices.
        shown: set[str] = set()
        for issue in fresh_issues:
            key = issue.firmware or issue.raw
            if key not in shown:
                shown.add(key)
                warn(f"Firmware diagnostic: {issue.raw[-300:]}")

    info("Step 7/7 — Updating the complete installed system...")
    if not apt_upgrade():
        return 1

    # Upgrade may have changed the kernel or firmware, so verify once more.
    time.sleep(1)
    verified_after, final_devices = verification(fresh)
    reboot = system_reboot_needed()
    if reboot:
        warn("A reboot is required to finish applying one or more system/kernel changes.")
    if verified_after:
        ok("Automatic hardware/driver maintenance finished successfully.")
    elif verified:
        warn("Installation completed, but one or more devices still need attention. The exact remaining state is shown above.")
    else:
        warn("Maintenance completed with unresolved driver state; no false SUCCESS is reported.")
    return 0 if (verified_after or not repairs) else 2


def main() -> int:
    banner()
    if not root():
        error("Run as root: sudo python3 kaliDriver.py")
        return 1
    print()
    if RICH:
        menu = Table(title="kaliDriver", box=box.ROUNDED, show_header=False, expand=False)
        menu.add_row("1", "Run")
        menu.add_row("2", "Exit")
        console.print(menu)
        choice = console.input("[bold cyan]Select: [/bold cyan]").strip()
    else:
        print("1 - Run\n2 - Exit")
        choice = input("Select: ").strip()
    if choice == "2":
        info("Exiting kaliDriver.")
        return 0
    if choice != "1":
        error("Please select 1 or 2.")
        return 1
    return full_run()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(130)
