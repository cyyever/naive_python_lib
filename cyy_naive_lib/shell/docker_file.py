#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.join(sys.path[0], ".."))


from fs.tempdir import TempDir
from system_info import get_operating_system

from .bash_script import BashScript
from .shell import Shell


class DockerFile(BashScript):
    def __init__(self, from_image: str, script: BashScript):
        self.content = ["FROM " + from_image]
        self.script = script
        self.throw_on_failure = True

    def _get_exec_command_line(self):
        raise RuntimeError("Unsupported")

    def build(
        self,
        result_image: str,
        src_dir_pair: tuple = None,
        use_experimental=False,
        additional_docker_commands: list = None,
        additional_ignored_files: list | None = None,
        extra_output_files=None,
    ):
        with TempDir():
            host_src_dir, docker_src_dir = None, None
            if src_dir_pair is not None:
                host_src_dir, docker_src_dir = src_dir_pair
                os.chdir(host_src_dir)
            if docker_src_dir is None:
                docker_src_dir = "/"

            script_name = "docker.sh"
            with open(script_name, "wt") as f:
                f.write(self.script.get_complete_content())
            script_path = os.path.join(docker_src_dir, script_name)

            with open("Dockerfile", "wt") as f:
                for line in self.content:
                    print(line, file=f)

                print("COPY . ", docker_src_dir, file=f)
                print("RUN bash " + script_path, file=f)
                if additional_docker_commands is not None:
                    for cmd in additional_docker_commands:
                        print(cmd, file=f)

            with open(".dockerignore", "wt", encoding="utf8") as f:
                print(".git", file=f)
                print("Dockerfile", file=f)
                if additional_ignored_files is not None:
                    for ignored_file in additional_ignored_files:
                        print(ignored_file, file=f)

            docker_cmd = ["docker", "build"]
            if get_operating_system() != "windows":
                docker_cmd.insert(0, "sudo")
            if use_experimental:
                docker_cmd.append("--squash")
            docker_cmd += [
                "-t",
                result_image,
                "-f",
                "Dockerfile",
                ".",
            ]
            output, exit_code = Shell.exec(
                docker_cmd, extra_output_files=extra_output_files
            )
            if self.throw_on_failure and exit_code != 0:
                raise RuntimeError("failed to build " + result_image)
            return output, exit_code
