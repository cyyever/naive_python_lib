#!/usr/bin/env python3

from .script import Script


class PowerShellScript(Script):
    def _wrap_content_in_strict_mode(self, content: str):
        return (
            self.line_seperator.join(
                [
                    "Set-StrictMode -Version Latest",
                    '$ErrorView="NormalView"',
                    '$ErrorActionPreference="Stop"',
                ]
            )
            + self.line_seperator
            + content
        )

    def _get_line_seperator(self):
        return "\r"

    def _export(self, key: str, value: str):
        if not value.startswith("'") and not value.startswith('"'):
            value = '"' + value + '"'
        value = value.replace("\\", "/")
        return "$env:" + key + "=" + value

    def _mkdir(self, path):
        return "mkdir -Force -Path " + path + " | Out-Null"
