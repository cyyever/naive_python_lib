#!/usr/bin/env python3

from shutil import which
from .bash_script import BashScript
from .shell import Shell


class DockerFile(BashScript):
    def _exec(self, from_image: str, result_image: str, src_dir: str = None):
        script_name = "docker.sh"
        with open(script_name, "w") as f:
            f.write(self.get_complete_content())

        with open("Dockerfile", "w") as f:
            print("FROM ", from_image, file=f)
            if src_dir is not None:
                print("RUN mkdir -p ", src_dir, file=f)
                print("COPY . ", src_dir, file=f)
            print("COPY ", script_name, " /", file=f)
            print("RUN bash /" + script_name, file=f)

        with open(".dockerignore", "w") as f:
            print(".git", file=f)
            print("Dockerfile", file=f)
            print("script.sh", file=f)

        cmd = []
        if which("sudo") != "windows":
            cmd.append("sudo")
        cmd.append("docker")
        cmd.append("build")
        cmd.append("-t")
        cmd.append(result_image)
        cmd.append("-f")
        cmd.append("Dockerfile")
        cmd.append(".")
        print(cmd)
        return Shell.exec(cmd)
