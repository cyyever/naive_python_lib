from .bash_script import BashScript


class Mingw64Script(BashScript):
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

    def _convert_path(self, path: str):
        path = path.replace("\\", "/")
        for driver in ["C", "D", "E", "F", "G", "H"]:
            if path.startswith(driver + ":"):
                return "/" + driver.lower() + path[2:]
        return path
