import subprocess
import sys
from io import BufferedReader
from threading import Thread
from time import sleep
from typing import TextIO


class Shell:
    @classmethod
    def exec(
        cls,
        command_line: list[str],
        print_out: bool = True,
        extra_output_files: list[TextIO] | None = None,
        **process_kwargs: object,
    ) -> tuple[str, int]:
        r"""
        Execute a command line
        """
        output_files: list[TextIO] = []
        if extra_output_files is not None:
            output_files = extra_output_files
        output_lines: list[str] = []
        with subprocess.Popen(
            command_line,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **process_kwargs,
        ) as proc:
            threads: list[Thread] = [
                Thread(
                    target=Shell.__output_text_line,
                    args=(
                        proc.stdout,
                        ([sys.stdout] if print_out else []) + output_files,
                        output_lines,
                    ),
                ),
                Thread(
                    target=Shell.__output_text_line,
                    args=(
                        proc.stderr,
                        ([sys.stderr] if print_out else []) + output_files,
                        None,
                    ),
                ),
            ]
            for thd in threads:
                thd.daemon = True
                thd.start()

            while True:
                alive = False
                for thd in threads:
                    if thd.is_alive():
                        alive = True
                        break
                if alive:
                    sleep(0.1)
                else:
                    break

            exit_code = proc.wait()
            for thd in threads:
                thd.join()
            return "\n".join(output_lines), exit_code

    @staticmethod
    def __decode_output(line: bytes) -> str:
        try:
            return line.decode("gb2312")
        # pylint: disable=broad-exception-caught
        except Exception:
            return line.decode("utf-8", errors="ignore")

    @staticmethod
    def __output_text_line(
        input_file: BufferedReader | None,
        output_files: list[TextIO],
        output_lines: list[str] | None,
    ) -> None:
        if input_file is None:
            return
        for line in iter(input_file.readline, b""):
            decoded_line = Shell.__decode_output(line)
            if output_lines is not None:
                output_lines.append(decoded_line)
            for f in output_files:
                f.write(decoded_line)
                f.flush()
