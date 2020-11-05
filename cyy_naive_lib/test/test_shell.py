import tempfile
import os
from shell_factory import exec_cmd
from shell.docker_file import DockerFile


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
        docker_file = DockerFile(content="ls")
        _, res = docker_file.exec(
            throw=False, from_image="ubuntu:latest", result_image="test_img"
        )
        os.chdir(cwd)
        assert res == 0
