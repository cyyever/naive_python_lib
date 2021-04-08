import os
import subprocess
import platform
from shutil import which
from util import readlines

__operating_system = None


def get_operating_system() -> str:
    global __operating_system

    def __impl():
        sys = platform.system().lower()
        if sys in ("windows", "freebsd"):
            return sys
        if sys == "linux":
            pf = platform.platform().lower()
            if "ubuntu" in pf:
                return "ubuntu"
            if which("pacman") is not None:
                return "archlinux"
            if which("apt-get") is not None:
                return "ubuntu"
            if os.path.isfile("/etc/centos-release"):
                return "centos"
            if os.path.isfile("/etc/fedora-release"):
                return "fedora"
            if which("lsb_release") is not None:
                output = (
                    subprocess.check_output("lsb_release -s -i", shell=True)
                    .decode("utf-8")
                    .strip()
                    .lower()
                )
                if "ubuntu" in output:
                    return "ubuntu"
        if sys == "darwin":
            return "macos"
        return None

    if __operating_system is None:
        __operating_system = __impl()
    return __operating_system


__processor_name = None


def get_processor_name() -> str:
    global __processor_name
    if __processor_name is not None:
        return __processor_name
    if os.path.isfile("/proc/cpuinfo"):
        __processor_name = [
            line.lower()
            for line in readlines("/proc/cpuinfo")
            if "model name" in line.lower()
        ][0]
    if __processor_name is None:
        if which("sysctl") is not None:
            output = os.popen("sysctl hw.model").read().lower()
            if output:
                if "intel" in output:
                    __processor_name = "intel"

    if __processor_name is None:
        __processor_name = platform.processor().lower()
    return __processor_name
