import os
from shutil import which

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.shell import exec_cmd, get_shell_script
from cyy_naive_lib.shell.bash_script import BashScript
from cyy_naive_lib.shell.docker_file import DockerFile
from cyy_naive_lib.shell.mingw64_script import Mingw64Script
from cyy_naive_lib.shell.msys2_script import MSYS2Script


def test_exec_cmd() -> None:
    with TempDir():
        _, res = get_shell_script("echo 'exec cmd' && ls").exec(throw=False)
        assert res == 0


def test_msys2_scriot() -> None:
    if which("msys2_shell.cmd"):
        MSYS2Script(content="pwd").exec()


def test_mingw64_scriot() -> None:
    if which("msys2_shell.cmd"):
        Mingw64Script(content="pwd").exec()


def test_unix_docker() -> None:
    if os.getenv("TEST_DOCKER") and which("docker") and exec_cmd("sudo docker ps"):
        with TempDir():
            bash_script = BashScript(content="ls")
            bash_script.append_env("PATH", "/root")
            docker_file = DockerFile(
                from_image="ubuntu:latest", script=bash_script, image_name="test_img"
            )
            _, res = docker_file.build()
            assert res == 0
