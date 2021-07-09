#!/usr/bin/env python3

from .bash_script import BashScript


class MSYS2Script(BashScript):
    def _get_exec_command_line(self):
        with open("script.sh", "w") as f:
            f.write(self.get_complete_content())
            return [
                "msys2_shell.cmd",
                "-msys",
                "-defterm",
                "-no-start",
                "-full-path",
                "-where",
                ".",
                "-c",
                "bash script.sh",
            ]
