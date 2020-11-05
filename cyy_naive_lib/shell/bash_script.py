#!/usr/bin/env python3

from .script import Script
from .shell import Shell


class BashScript(Script):
    def get_suffix(self) -> str:
        return "sh"

    def exec(self):
        with open("script.sh", "w") as f:
            f.write(self.get_complete_content())
        return Shell._exec(["bash", "script.sh"])

    def _wrap_content_in_strict_mode(
            self,
            env_part: str,
            content_part: str) -> str:
        return (
            self.line_seperator.join(["set -eu", "set -o pipefail"])
            + self.line_seperator
            + env_part
            + self.line_seperator
            + content_part
        )

    def _export(self, key, value):
        if key == "PATH":
            return "export PATH=" + \
                self.__double_quota_escape_str(value) + ":${PATH}"
        return (
            "if [[ -z ${"
            + key
            + "+x}  ]]; then export "
            + key
            + "="
            + self.__double_quota_escape_str(value)
            + "; fi"
        )

    def _get_line_seperator(self):
        return "\n"

    def __double_quota_escape_str(self, string):
        escaped_str = ""
        escaped_str += '"'
        for a in string:
            if a == '"':
                escaped_str += "\\"
            escaped_str += a
        escaped_str += '"'
        return escaped_str

    def _mkdir(self, path):
        return "mkdir -p " + path
