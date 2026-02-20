import functools
import os
import platform
import subprocess
from enum import StrEnum, auto
from shutil import which


class OSType(StrEnum):
    Windows = auto()
    FreeBSD = auto()
    Ubuntu = auto()
    ArchLinux = auto()
    CentOS = auto()
    RedHat = auto()
    Fedora = auto()
    MacOS = auto()
    Linux = auto()


def _detect_linux_distro() -> OSType:
    try:
        info = platform.freedesktop_os_release()
        ids = info.get("ID", "") + " " + info.get("ID_LIKE", "")
        ids = ids.lower()
        if "ubuntu" in ids or "debian" in ids:
            return OSType.Ubuntu
        if "arch" in ids:
            return OSType.ArchLinux
        if "centos" in ids:
            return OSType.CentOS
        if "fedora" in ids:
            return OSType.Fedora
        if "rhel" in ids or "redhat" in ids:
            return OSType.RedHat
    except OSError:
        pass
    return OSType.Linux


@functools.cache
def get_operating_system_type() -> OSType:
    match platform.system().lower():
        case "windows":
            return OSType.Windows
        case "freebsd":
            return OSType.FreeBSD
        case "darwin":
            return OSType.MacOS
        case "linux":
            return _detect_linux_distro()
        case sys:
            raise RuntimeError(f"Unknown OS: {sys}")


@functools.cache
def get_operating_system() -> str:
    return get_operating_system_type().value


@functools.cache
def get_processor_name() -> str:
    # platform.processor() is empty on Linux, unreliable on macOS
    if os.path.isfile("/proc/cpuinfo"):
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if "model name" in line.lower():
                    return line.strip().lower()
    if which("sysctl") is not None:
        try:
            output = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
            ).strip()
            if output:
                return output.lower()
        except (subprocess.CalledProcessError, OSError):
            pass
    return platform.processor() or platform.machine()
