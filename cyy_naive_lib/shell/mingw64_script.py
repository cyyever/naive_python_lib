#!/usr/bin/env python3

from .msys2_script import MSYS2Script


class Mingw64Script(MSYS2Script):
    def _get_exec_command_line(self):
        with open("script.sh", "w") as f:
            f.write(self.get_complete_content())
            return [
                "msys2_shell.cmd",
                "-mingw64",
                "-defterm",
                "-no-start",
                "-where",
                ".",
                "-c",
                "bash script.sh",
            ]

