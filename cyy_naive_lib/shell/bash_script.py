from .script import Script


class BashScript(Script):
    def get_suffix(self) -> str:
        return "sh"

    def _get_exec_command_line(self) -> dict:
        script_name = self._get_temp_script_name()
        with open(script_name, "w", encoding="utf8") as f:
            f.write(self.get_complete_content())
            return {"cmd": ["bash", script_name], "script_name": script_name}

    def _wrap_content_in_strict_mode(self, env_part: str, content_part: str) -> str:
        return (
            self.line_separator.join(["set -eu", "set -o pipefail"])
            + self.line_separator
            + env_part
            + self.line_separator
            + content_part
        )

    def _export(self, key: str, value: str) -> str:
        for special_key in ("PATH", "LD_LIBRARY_PATH"):
            if key == special_key:
                return (
                    "if [[ -z ${"
                    + key
                    + "+x}  ]]; then export "
                    + key
                    + "="
                    + self.__double_quota_escape_str(value)
                    + "; else export "
                    + key
                    + "="
                    + self.__double_quota_escape_str(value)
                    + ":${"
                    + key
                    + "} ; fi"
                )
        return "export " + key + "=" + self.__double_quota_escape_str(value)

    def _get_line_separator(self) -> str:
        return "\n"

    def __double_quota_escape_str(self, string: str) -> str:
        escaped_str = ""
        escaped_str += '"'
        for a in string:
            if a == '"':
                escaped_str += "\\"
            escaped_str += a
        escaped_str += '"'
        return escaped_str
