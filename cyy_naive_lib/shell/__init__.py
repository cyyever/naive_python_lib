from ..system_info import OSType, get_operating_system_type
from .bash_script import BashScript
from .mingw64_script import Mingw64Script
from .msys2_script import MSYS2Script
from .pwsh_script import PowerShellScript
from .script import Script


def get_shell_script_type(os_hint: OSType | None = None) -> type:
    if os_hint is None:
        os_hint = get_operating_system_type()
    if os_hint == OSType.Windows:
        return PowerShellScript
    return BashScript


def get_shell_script(content: str, os_hint: OSType | None = None) -> Script:
    return get_shell_script_type(os_hint)(content)


def exec_cmd(
    cmd: str,
    os_hint: OSType | None = None,
    throw: bool = True,
) -> tuple[str, int]:
    return get_shell_script(cmd, os_hint=os_hint).exec(throw=throw)


__all__ = [
    "BashScript",
    "MSYS2Script",
    "Mingw64Script",
    "PowerShellScript",
    "exec_cmd",
    "get_shell_script",
    "get_shell_script_type",
]
