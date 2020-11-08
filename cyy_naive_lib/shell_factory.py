#!/usr/bin/env python3

from system_info import get_operating_system
from shell.script import Script
from shell.pwsh_script import PowerShellScript
from shell.bash_script import BashScript


def get_shell_script_type(os_hint: str = None) -> Script:
    if os_hint is None:
        os_hint = get_operating_system()
    if os_hint == "windows":
        return PowerShellScript
    return BashScript


def get_shell_script(os_hint: str = None) -> Script:
    return get_shell_script_type(os_hint)()


def exec_cmd(cmd: str, throw: bool = True):
    output, exit_code = get_shell_script_type()(cmd).exec(throw=False)
    if throw and exit_code != 0:
        raise RuntimeError("failed to execute commands:" + str(cmd))
    return output, exit_code
