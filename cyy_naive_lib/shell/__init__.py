from typing import Any

from ..system_info import OSType, get_operating_system_type
from .bash_script import BashScript
from .mingw64_script import Mingw64Script
from .msys2_script import MSYS2Script
from .pwsh_script import PowerShellScript
from .script import Script

__all__ = [
    "BashScript",
    "Mingw64Script",
    "PowerShellScript",
    "MSYS2Script",
    "get_shell_script_type",
    "get_shell_script",
    "exec_cmd",
]


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
) -> tuple[Any, int]:
    return get_shell_script(cmd, os_hint=os_hint).exec(throw=throw)
