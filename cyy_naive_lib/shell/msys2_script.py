from .mingw64_script import Mingw64Script


class MSYS2Script(Mingw64Script):
    def _get_exec_command_line(self) -> dict:
        res = super()._get_exec_command_line()
        idx = res["cmd"].index("-mingw64")
        res["cmd"][idx] = "-msys"
        return res
