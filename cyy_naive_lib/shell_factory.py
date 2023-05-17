from .shell.bash_script import BashScript
from .shell.pwsh_script import PowerShellScript
from .shell.script import Script
from .system_info import get_operating_system


def get_shell_script_type(os_hint: str | None = None) -> Script:
    if os_hint is None:
        os_hint = get_operating_system()
    if os_hint == "windows":
        return PowerShellScript
    return BashScript


def get_shell_script(content: str, os_hint: str | None = None) -> Script:
    return get_shell_script_type(os_hint)(content)


def exec_cmd(cmd: str, os_hint: str | None = None, throw: bool = True) -> tuple:
    output, exit_code = get_shell_script(cmd).exec(throw=False)
    if throw and exit_code != 0:
        raise RuntimeError(f"failed to execute commands: {cmd} \n outputs: {output}")
    return output, exit_code
