from shutil import which

from cyy_naive_lib.fs.tempdir import TempDir
from cyy_naive_lib.shell.mingw64_script import Mingw64Script
# from shell.bash_script import BashScript
# from shell.docker_file import DockerFile
from cyy_naive_lib.shell.msys2_script import MSYS2Script
from cyy_naive_lib.shell_factory import get_shell_script


def test_exec_cmd():
    with TempDir():
        _, res = get_shell_script("echo 'exec cmd' && ls").exec(throw=False)
        assert res == 0


def test_msys2_scriot():
    if which("msys2_shell.cmd"):
        MSYS2Script(content="pwd").exec()


def test_mingw64_scriot():
    if which("msys2_shell.cmd"):
        Mingw64Script(content="pwd").exec()


# def test_unix_docker():
#     if which("systemctl") and which("docker"):
#         with TempDir():
#             _, res = exec_cmd("sudo systemctl start docker", throw=False)
#             bash_script = BashScript(content="ls")
#             bash_script.append_env("PATH", "/root")
#             docker_file = DockerFile(from_image="ubuntu:latest", script=bash_script)
#             docker_file.throw_on_failure = False
#             _, res = docker_file.build(result_image="test_img")
#             assert res == 0
