import os
from collections.abc import Iterable
from typing import Any, TextIO

from .shell import Shell


class Script:
    def __init__(self, content: str | Iterable[str] | None = None) -> None:
        self.content: list = []
        if content is not None:
            self.append_content(content)
        self.env: list = []
        self.strict_mode: bool = True
        self.line_separator: str = self._get_line_separator()

    def append_env(self, key: str, value: str) -> None:
        r"""
        Add an environment variable to the script
        """
        self.env.append((key, value))

    def prepend_env(self, key: str, value: str) -> None:
        r"""
        Add an environment variable to the script
        """
        self.env = [(key, value)] + self.env

    def append_env_path(self, key: str, value: str) -> None:
        self.append_env(key, self._convert_path(value))

    def prepend_env_path(self, key: str, value: str) -> None:
        self.prepend_env(key, self._convert_path(value))

    def _convert_path(self, path: str) -> str:
        return path

    def prepend_content(self, content: str | Iterable) -> None:
        if isinstance(content, str):
            self.content = content.splitlines() + self.content
        else:
            self.content = list(content) + self.content
        self.__remove_newline()

    def append_content(self, content: str | Iterable[str]) -> None:
        if isinstance(content, str):
            self.content += content.splitlines()
        else:
            self.content += list(content)
        self.__remove_newline()

    def get_suffix(self) -> str:
        raise NotImplementedError()

    def _get_temp_script_name(self) -> str:
        for idx in range(10000):
            path = f"script{idx}.{self.get_suffix()}"
            if not os.path.isfile(path):
                return path
        raise RuntimeError("Can't create script name")

    def get_complete_content(self) -> str:
        env_part = self.line_separator.join([self._export(k, v) for (k, v) in self.env])
        content_part = self.line_separator.join(self.content)

        if self.strict_mode:
            return self._wrap_content_in_strict_mode(env_part, content_part)
        return env_part + self.line_separator + content_part

    def exec(
        self,
        throw: bool = True,
        extra_output_files: None | list[TextIO] = None,
        **exec_kwargs,
    ) -> tuple[Any, int]:
        res = self._get_exec_command_line()
        output, exit_code = Shell.exec(
            command_line=res["cmd"],
            extra_output_files=extra_output_files,
            **exec_kwargs,
        )
        if os.path.isfile(res["script_name"]):
            os.remove(res["script_name"])
        if throw and exit_code != 0:
            raise RuntimeError("failed to execute script")
        return output, exit_code

    def _get_exec_command_line(self):
        raise NotImplementedError()

    def _wrap_content_in_strict_mode(self, env_part: str, content_part: str) -> str:
        raise NotImplementedError()

    def _export(self, key: str, value: str) -> str:
        r"""
        Return an command to export the environment variable
        """
        raise NotImplementedError()

    def _get_line_separator(self) -> str:
        raise NotImplementedError()

    def __remove_newline(self) -> None:
        self.content = [line.rstrip("\r\n") for line in self.content]
