#!/usr/bin/env python3

from .script import Script
from .shell import Shell


class PowerShellScript(Script):
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

    def exec(self):
        with open("script.ps1", "w") as f:
            f.write(self.get_complete_content())
        return Shell._exec(["pwsh", "-NoProfile", "-File", "script.ps1"])

    def _export(self, key: str, value: str):
        if not value.startswith("'") and not value.startswith('"'):
            value = '"' + value + '"'
        value = value.replace("\\", "/")
        return "$env:" + key + "=" + value

    def _mkdir(self, path):
        return "mkdir -Force -Path " + path + " | Out-Null"
