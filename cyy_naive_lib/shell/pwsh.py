#!/usr/bin/env python3

from .shell import Shell
from .pwsh_script import PowerShellScript


class PowerShell(Shell):
    def _exec_script(self, script):
        if not isinstance(script, PowerShellScript):
            script = PowerShellScript(content=script)
        with open("script.ps1", "w") as f:
            f.write(script.get_complete_content())
        return self._exec(["pwsh", "-NoProfile", "-File", "script.ps1"])
