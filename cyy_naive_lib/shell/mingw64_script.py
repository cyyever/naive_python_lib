from .msys2_script import MSYS2Script


class Mingw64Script(MSYS2Script):
    def _get_exec_command_line(self):
        res = super()._get_exec_command_line()
        res["cmd"] = [
            "msys2_shell.cmd",
            "-mingw64",
            "-defterm",
            "-no-start",
            "-where",
            ".",
            "-c",
            " ".join(res["cmd"]),
        ]
        return res
