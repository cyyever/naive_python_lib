#!/usr/bin/env python3


class Script:
    def __init__(self, content: str = None, path: str = None):
        self.content = None
        if content is not None:
            self.content = content.splitlines()
        if path is not None:
            if self.content is not None:
                raise RuntimeError("can't specify both content and path")
            with open(path, "rt") as f:
                self.content = f.readlines()

        self.env: list = []
        self.strict_mode = True
        self.line_seperator = self._get_line_seperator()

    def append_env(self, key: str, value: str):
        r"""
        Add an environment variable to the script
        """
        self.env.append((key, value))

    def get_complete_content(self):
        content = self.line_seperator.join(
            [self._export(k, v) for (k, v) in self.env] + self.content
        )

        if self.strict_mode:
            return self._wrap_content_in_strict_mode(content)
        return content

    def _wrap_content_in_strict_mode(self, content: str):
        raise NotImplementedError()

    def _export(self, key: str, value: str):
        r"""
        Return an command to export the environment variable
        """
        raise NotImplementedError()

    def _get_line_seperator(self) -> str:
        raise NotImplementedError()
