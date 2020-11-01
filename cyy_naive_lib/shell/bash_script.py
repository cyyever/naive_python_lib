#!/usr/bin/env python3

from .script import Script


class BashScript(Script):
    def _wrap_content_in_strict_mode(self, content: str):
        return (
            self.line_seperator.join(["set -eu", "set -o pipefail"])
            + self.line_seperator
            + content
        )

    def _export(self, key, value):
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
