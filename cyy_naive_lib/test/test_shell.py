import tempfile
import os
from shell_factory import exec_cmd
from shell.docker_file import DockerFile
from shell.bash_script import BashScript


def test_exec_cmd():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        _, res = exec_cmd("ls", throw=False)
        os.chdir(cwd)
        assert res == 0


def test_docker():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        _, res = exec_cmd("sudo systemctl start docker", throw=False)
        bash_script = BashScript(content="ls")
        bash_script.append_env("PATH", "/root")
        docker_file = DockerFile(
            from_image="ubuntu:latest",
            script=bash_script)
        docker_file.throw_on_failure = False
        _, res = docker_file.build(result_image="test_img")
        os.chdir(cwd)
        assert res == 0
