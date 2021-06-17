#!/usr/bin/env python3


from shell.bash_script import BashScript
from shell.pwsh_script import PowerShellScript
from shell.script import Script
from system_info import get_operating_system


def get_shell_script_type(os_hint: str = None) -> Script:
    if os_hint is None:
        os_hint = get_operating_system()
    if os_hint == "windows":
        return PowerShellScript
    return BashScript


def get_shell_script(content: str = None, os_hint: str = None) -> Script:
    return get_shell_script_type(os_hint)(content)


def exec_cmd(cmd: str, throw: bool = True):
    shell_script = get_shell_script_type()
    output, exit_code = shell_script(cmd).exec(throw=False)
    if throw and exit_code != 0:
        raise RuntimeError("failed to execute commands:" + str(cmd))
    return output, exit_code
