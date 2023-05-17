import os

from ..fs.tempdir import TempDir
from ..system_info import get_operating_system
from .bash_script import BashScript
from .shell import Shell


class DockerFile:
    def __init__(
        self,
        from_image: str,
        image_name: str,
        script: BashScript,
        use_experimental: bool = False,
    ):
        self.content = ["FROM " + from_image]
        self.image_name = image_name
        self.script = script
        self.use_experimental = use_experimental

    def build(
        self,
        src_dir_pair: tuple | None = None,
        additional_docker_commands: list | None = None,
        docker_ignored_files: list | None = None,
        exec_kwargs: dict | None = None,
    ):
        with TempDir():
            host_src_dir, docker_src_dir = None, None
            if src_dir_pair is not None:
                host_src_dir, docker_src_dir = src_dir_pair
                os.chdir(host_src_dir)
            if docker_src_dir is None:
                docker_src_dir = "/"

            script_name = "docker.sh"
            with open(script_name, "wt", encoding="utf8") as f:
                f.write(self.script.get_complete_content())
            script_path = os.path.join(docker_src_dir, script_name)

            with open("Dockerfile", "wt", encoding="utf8") as f:
                for line in self.content:
                    print(line, file=f)

                if host_src_dir is not None:
                    print("COPY . ", docker_src_dir, file=f)
                else:
                    print("COPY docker.sh ", docker_src_dir, file=f)
                print("RUN bash " + script_path, file=f)
                if additional_docker_commands is not None:
                    for cmd in additional_docker_commands:
                        print(cmd, file=f)

            with open(".dockerignore", "wt", encoding="utf8") as f:
                print(".git", file=f)
                print("Dockerfile", file=f)
                if docker_ignored_files is not None:
                    for ignored_file in docker_ignored_files:
                        print(ignored_file, file=f)

            docker_cmd = ["docker", "build"]
            if get_operating_system() != "windows":
                docker_cmd.insert(0, "sudo")
            if self.use_experimental:
                docker_cmd.append("--squash")
            docker_cmd += [
                "-t",
                self.image_name,
                "-f",
                "Dockerfile",
                ".",
            ]
            if exec_kwargs:
                return Shell.exec(docker_cmd, **exec_kwargs)
            return Shell.exec(docker_cmd)
