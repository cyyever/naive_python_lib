#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from threading import Thread
from time import sleep


class Shell:
    @staticmethod
    def exec(command_line: list):
        r"""
        Execute a command line
        """
        with tempfile.NamedTemporaryFile() as output_file:
            with subprocess.Popen(
                command_line,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as proc:
                threads = [
                    Thread(
                        target=Shell.__process_stdout, args=(proc.stdout, output_file)
                    ),
                    Thread(
                        target=Shell.__process_stderr, args=(proc.stderr, output_file)
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
                return [Shell.__decode_output(output_file.read()), exit_code]

    @staticmethod
    def __decode_output(line):
        try:
            return line.decode("gb2312")
        except Exception:
            return line.decode("utf-8", errors="ignore")

    @staticmethod
    def __process_stdout(proc_out, store_file):
        for line in iter(proc_out.readline, b""):
            sys.stdout.write(Shell.__decode_output(line))
            store_file.write(line)
            store_file.flush()

    @staticmethod
    def __process_stderr(proc_err, store_file):
        for line in iter(proc_err.readline, b""):
            sys.stderr.write(Shell.__decode_output(line))
            store_file.write(line)
            store_file.flush()
