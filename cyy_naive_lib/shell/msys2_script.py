from .mingw64_script import Mingw64Script
from .script import ExecCommandLine


class MSYS2Script(Mingw64Script):
    def _get_exec_command_line(self) -> ExecCommandLine:
        res = super()._get_exec_command_line()
        idx = res["cmd"].index("-mingw64")
        res["cmd"][idx] = "-msys"
        return res
