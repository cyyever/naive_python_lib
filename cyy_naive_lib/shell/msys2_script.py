#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.join(sys.path[0], ".."))

from fs.tempdir import TempDir

from .bash_script import BashScript
from .shell import Shell

class MSYS2Script(BashScript):
    def _exec(self):
        with TempDir():
            with open("script.sh", "w") as f:
                f.write(self.get_complete_content())
            return Shell.exec(
                [
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
            )
