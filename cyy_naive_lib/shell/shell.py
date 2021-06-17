#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from threading import Thread
from time import sleep


class Shell:
    @staticmethod
    def exec(command_line: list, extra_output_files=None):
        r"""
        Execute a command line
        """
        with tempfile.NamedTemporaryFile(mode="w+t") as output_file:
            output_files = []
            if extra_output_files is not None:
                output_files = extra_output_files
            output_files.append(output_file)
            with subprocess.Popen(
                command_line,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as proc:
                threads = [
                    Thread(
                        target=Shell.__output_text_line,
                        args=(proc.stdout, [sys.stdout] + output_files),
                    ),
                    Thread(
                        target=Shell.__output_text_line,
                        args=(proc.stderr, [sys.stderr] + output_files),
                    ),
                ]
                for thd in threads:
                    thd.setDaemon(True)
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
                output_file.seek(0, 0)
                return [output_file.read(), exit_code]

    @staticmethod
    def __decode_output(line):
        try:
            return line.decode("gb2312")
        except Exception:
            return line.decode("utf-8", errors="ignore")

    @staticmethod
    def __output_text_line(input_file, output_files):
        for line in iter(input_file.readline, b""):
            decoded_line = Shell.__decode_output(line)
            for f in output_files:
                f.write(decoded_line)
                f.flush()
