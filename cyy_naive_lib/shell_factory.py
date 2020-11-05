#!/usr/bin/env python3

from system_info import get_operating_system
from shell.script import Script
from shell.pwsh_script import PowerShellScript
from shell.bash_script import BashScript


def get_shell_script() -> Script:
    if get_operating_system() == "windows":
        return PowerShellScript
    return BashScript


def exec_cmd(cmd: str, throw: bool = True):
    output, exit_code = get_shell_script()(cmd).exec()
    if throw and exit_code != 0:
        raise RuntimeError("failed to execute commands:" + str(cmd))
    return output, exit_code


def exec_script(script: Script, throw=True):
    output, exit_code = script().exec()
    if throw and exit_code != 0:
        raise RuntimeError("failed to execute script")
    return output, exit_code
