#!/usr/bin/env python3

from .shell import Shell


class Script:
    def __init__(self, content: str = None):
        self.content: list = []
        if content is not None:
            self.append_content(content)
        self.env: list = []
        self.strict_mode = True
        self.line_seperator = self._get_line_seperator()

    def append_env(self, key: str, value: str):
        r"""
        Add an environment variable to the script
        """
        self.env.append((key, value))

    def prepend_env(self, key: str, value: str):
        r"""
        Add an environment variable to the script
        """
        self.env = [(key, value)] + self.env

    def append_env_path(self, key: str, value: str):
        self.append_env(key, value)

    def prepend_env_path(self, key: str, value: str):
        self.prepend_env(key, value)

    def prepend_content(self, content):
        if isinstance(content, list):
            self.content = content + self.content
        elif isinstance(content, str):
            self.content = content.splitlines() + self.content
        else:
            raise RuntimeError("unsupported content type")
        self.__remove_newline()

    def append_content(self, content):
        if isinstance(content, list):
            self.content += content
        elif isinstance(content, str):
            self.content += content.splitlines()
        else:
            raise RuntimeError("unsupported content type")
        self.__remove_newline()

    def get_suffix(self) -> str:
        raise NotImplementedError()

    def get_complete_content(self):
        env_part = self.line_seperator.join([self._export(k, v) for (k, v) in self.env])
        content_part = self.line_seperator.join(self.content)

        if self.strict_mode:
            return self._wrap_content_in_strict_mode(env_part, content_part)
        return env_part + self.line_seperator + content_part

    def exec(self, throw=True, extra_output_files=None):
        output, exit_code = Shell.exec(
            command_line=self._get_exec_command_line(),
            extra_output_files=extra_output_files,
        )
        if throw and exit_code != 0:
            raise RuntimeError("failed to execute script")
        return output, exit_code

    def _get_exec_command_line(self):
        raise NotImplementedError()

    def _wrap_content_in_strict_mode(self, env_part: str, content_part: str):
        raise NotImplementedError()

    def _export(self, key: str, value: str):
        r"""
        Return an command to export the environment variable
        """
        raise NotImplementedError()

    def _get_line_seperator(self) -> str:
        raise NotImplementedError()

    def __remove_newline(self):
        self.content = [line.rstrip("\r\n") for line in self.content]
