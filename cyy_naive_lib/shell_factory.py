#!/usr/bin/env python3

from system_info import get_operating_system
from shell.shell import Shell
from shell.bash import Bash
from shell.pwsh import PowerShell


def get_shell() -> Shell:
    if get_operating_system() == "Windows":
        return PowerShell()
    return Bash()


def exec_cmd(cmd: str, throw: bool = True):
    output, exit_code = get_shell().exec(cmd)
    if throw and exit_code != 0:
        raise RuntimeError("failed to execute commands:" + str(cmd))
    return output, exit_code


def exec_script(script_path, throw=True):
    with open(script_path, "r") as f:
        return exec_cmd(f.read(), throw)
