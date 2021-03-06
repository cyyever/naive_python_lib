#!/usr/bin/env python3

from shutil import which
from .bash_script import BashScript
from .shell import Shell


class DockerFile(BashScript):
    def __init__(self, from_image: str, script: BashScript):
        self.content = ["FROM " + from_image]
        self.script = script
        self.throw_on_failure = True

    def build(
        self,
        result_image: str,
        src_dir: str = None,
        additional_docker_commands: list = None,
    ):
        script_name = "docker.sh"
        with open(script_name, "wt") as f:
            f.write(self.script.get_complete_content())

        with open("Dockerfile", "wt") as f:
            for line in self.content:
                print(line, file=f)

            if src_dir is not None:
                print("RUN mkdir -p ", src_dir, file=f)
                print("COPY . ", src_dir, file=f)
            print("COPY ", script_name, " /", file=f)
            print("RUN bash /" + script_name, file=f)
            print("RUN rm /" + script_name, file=f)
            if additional_docker_commands is not None:
                for cmd in additional_docker_commands:
                    print(cmd, file=f)

        with open(".dockerignore", "w") as f:
            print(".git", file=f)
            print("Dockerfile", file=f)

        cmd = []
        if which("sudo") != "windows":
            cmd.append("sudo")
        cmd += ["docker", "build", "-t", result_image, "-f", "Dockerfile", "."]
        output, exit_code = Shell.exec(cmd)
        if self.throw_on_failure and exit_code != 0:
            raise RuntimeError("failed to build " + result_image)
        return output, exit_code
