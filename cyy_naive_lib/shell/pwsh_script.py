import re

from .script import Script, ExecCommandLine


class PowerShellScript(Script):
    def __init__(self, content: str | None = None) -> None:
        super().__init__(content=content)
        self.use_bash_stype_env_var = True

    def _wrap_content_in_strict_mode(self, env_part: str, content_part: str):
        return (
            self.line_separator.join(
                [
                    "Set-StrictMode -Version Latest",
                    '$ErrorView="NormalView"',
                    '$ErrorActionPreference="Stop"',
                ]
            )
            + self.line_separator
            + env_part
            + self.line_separator
            + content_part
        )

    def _get_line_separator(self) -> str:
        return "\r\n"

    def get_suffix(self) -> str:
        return "ps1"

    def _get_exec_command_line(self) -> ExecCommandLine:
        script_name = self._get_temp_script_name()
        with open(script_name, "w", encoding="utf8") as f:
            f.write(self.get_complete_content())
        return {
            "cmd": ["pwsh", "-NoProfile", "-File", script_name],
            "script_name": script_name,
        }

    def _export(self, key: str, value: str):
        if value.startswith("(") and value.endswith(")"):
            pass
        elif not value.startswith("'") and not value.startswith('"'):
            value = '"' + value + '"'
        value = value.replace("\\", "/")
        if self.use_bash_stype_env_var:
            p = re.compile(r"\$\{([^}]*)\}")
            value = p.sub(r"${env:\1}", value)
        return "$env:" + key + "=" + value
