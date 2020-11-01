import os
import subprocess
import platform
from shutil import which

__operating_system = None


def get_operating_system():
    global __operating_system

    def __impl():
        sys = platform.system().lower()
        if sys in ("windows", "freebsd"):
            return sys
        pf = platform.platform().lower()
        if sys == "linux":
            if "ubuntu" in pf:
                return "ubuntu"
            if which("pacman") is not None:
                return "archlinux"
            if which("apt-get") is not None:
                return "ubuntu"
            if os.path.isfile("/etc/centos-release"):
                return "centos"
            if which("lsb_release") is not None:
                output = (
                    subprocess.check_output("lsb_release -s -i", shell=True)
                    .decode("utf-8")
                    .strip()
                    .lower()
                )
                if "ubuntu" in output:
                    return "ubuntu"
        return pf

    if __operating_system is None:
        __operating_system = __impl()
    return __operating_system
