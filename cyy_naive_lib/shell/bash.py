#!/usr/bin/env python3

from .shell import Shell
from .bash_script import BashScript


class Bash(Shell):
    def _exec_script(self, script):
        if not isinstance(script, BashScript):
            script = BashScript(content=script)
        with open("script.sh", "w") as f:
            f.write(script.get_complete_content())
        return self._exec(["bash", "script.sh"])
