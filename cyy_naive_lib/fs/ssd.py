# Forked from git@github.com:kipodd/ssd_checker.git
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _fullpath(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _is_nt_ssd(path: str | Path) -> bool:
    try:
        drive = os.path.splitdrive(_fullpath(path))[0]
        if not drive:
            return True
        # Get the physical disk MediaType for the drive letter
        script = (
            f"$d = Get-Partition -DriveLetter '{drive[0]}' | Get-Disk; "
            f"$d | Get-PhysicalDisk | Select-Object -Property MediaType | ConvertTo-Json"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return True
        data = json.loads(result.stdout.strip())
        media_type = data.get("MediaType", "")
        # "SSD" = solid state, "Unspecified" = often NVMe, "HDD" = rotational
        return media_type != "HDD"
    except Exception:
        return True


def _is_osx_ssd(path: str | Path) -> bool:
    return True


def _is_posix_ssd(path: str | Path) -> bool:
    block = _blkdevice(path)
    if block is None:
        return False
    sys_path = Path(f"/sys/block/{block}/queue/rotational")
    if not sys_path.is_file():
        m = re.search(r"p\d+$", block)
        if m:
            sys_path = Path(f"/sys/block/{block[: m.start()]}/queue/rotational")
    try:
        return sys_path.read_text(encoding="ascii").strip() == "0"
    except OSError:
        return False


def _get_parent_device_id(device_id: int) -> str:
    major = os.major(device_id)  # type: ignore[attr-defined]
    minor = os.minor(device_id)  # type: ignore[attr-defined]

    # For some device types, a block entry does not exist for partitions.
    # The minor device ID of the "whole disk" entry is given by the upper N
    # bits of the partition minor device ID.
    #
    # Only SCSI and IDE devices are handled.
    #
    # https://www.kernel.org/doc/Documentation/admin-guide/devices.txt

    MAJOR_DEVICE_IDS_IDE = (3, 22, 33, 34, 56, 57, 88, 89, 90, 91)
    MAJOR_DEVICE_IDS_SCSI = (
        8,
        65,
        66,
        67,
        68,
        69,
        70,
        71,
        128,
        129,
        130,
        131,
        132,
        133,
        134,
        135,
    )

    if major in MAJOR_DEVICE_IDS_IDE:
        disk_id = minor >> 6
        minor = disk_id * 64
    elif major in MAJOR_DEVICE_IDS_SCSI:
        # SCSI devices
        disk_id = minor >> 4
        minor = disk_id * 16

    return f"{major}:{minor}"


def _blkdevice(path: str | Path) -> str | None:
    device_id = _get_parent_device_id(_fullpath(path).stat().st_dev)

    for device_path in Path("/sys/class/block").glob("*/dev"):
        if device_path.read_text(encoding="utf8").strip() == device_id:
            return device_path.parent.name
    return None


if os.name == "nt":
    is_ssd = _is_nt_ssd
elif sys.platform == "darwin":
    is_ssd = _is_osx_ssd
else:
    is_ssd = _is_posix_ssd
