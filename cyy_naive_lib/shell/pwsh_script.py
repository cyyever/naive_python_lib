#!/usr/bin/env python3
import re

from .script import Script


class PowerShellScript(Script):
    def __init__(self, content: str = None):
        super().__init__(content=content)
        self.use_bash_stype_env_var = True

    def _wrap_content_in_strict_mode(self, env_part: str, content_part: str):
        return (
            self.line_seperator.join(
                [
                    "Set-StrictMode -Version Latest",
                    '$ErrorView="NormalView"',
                    '$ErrorActionPreference="Stop"',
                ]
            )
            + self.line_seperator
            + env_part
            + self.line_seperator
            + content_part
        )

    def _get_line_seperator(self):
        return "\r"

    def get_suffix(self) -> str:
        return "ps1"

    def _get_exec_command_line(self):
        with open("script.ps1", "w") as f:
            f.write(self.get_complete_content())
            return ["pwsh", "-NoProfile", "-File", "script.ps1"]

    def _export(self, key: str, value: str):
        if value.startswith("(") and value.endswith(")"):
            pass
        elif not value.startswith("'") and not value.startswith('"'):
            value = '"' + value + '"'
        value = value.replace("\\", "/")
        if self.use_bash_stype_env_var:
            p = re.compile(r"\$\{([^}]*)\}")
            value = p.sub(r"$env:\1", value)
        return "${env:" + key + "}=" + value
