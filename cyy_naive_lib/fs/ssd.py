# Forked from git@github.com:kipodd/ssd_checker.git
import os
import sys
from glob import glob
from os.path import basename, dirname, expanduser, realpath


def _fullpath(path):
    return realpath(expanduser(path))


def _get_parent_device_id(device_id) -> str:
    major = os.major(device_id)
    minor = os.minor(device_id)

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


def _blkdevice(path):
    device_id = _get_parent_device_id(os.stat(_fullpath(path)).st_dev)
    block = ""

    for device in glob("/sys/class/block/*/dev"):
        with open(device, encoding="utf8") as f:
            if f.read().strip() == device_id:
                block = basename(dirname(device))
                return block
    return None


def _is_nt_ssd(path):
    return True


def _is_osx_ssd(path) -> bool:
    return True


def _is_posix_ssd(path: str) -> bool:
    block = _blkdevice(path)
    if block is None:
        return False
    path = f"/sys/block/{block}/queue/rotational"
    if not os.path.isfile(path):
        for i in range(10):
            if block.endswith(f"p{i}"):
                path = f"/sys/block/{block[:-2]}/queue/rotational"
                break
    try:
        with open(path, encoding="ascii") as fp:
            return fp.read().strip() == "0"

    except OSError:
        return False


if os.name == "nt":
    is_ssd = _is_nt_ssd
elif sys.platform == "darwin":
    is_ssd = _is_osx_ssd
else:
    is_ssd = _is_posix_ssd
