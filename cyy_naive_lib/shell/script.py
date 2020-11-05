#!/usr/bin/env python3


class Script:
    def __init__(self, content=None):
        self.content = []
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
        env_part = self.line_seperator.join(
            [self._export(k, v) for (k, v) in self.env])
        content_part = self.line_seperator.join(self.content)

        if self.strict_mode:
            return self._wrap_content_in_strict_mode(env_part, content_part)
        return env_part + self.line_seperator + content_part

    def exec(self, throw=True, *args, **kwargs):
        output, exit_code = self._exec(*args, **kwargs)
        if throw and exit_code != 0:
            raise RuntimeError("failed to execute script")
        return output, exit_code

    def _exec(self):
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
