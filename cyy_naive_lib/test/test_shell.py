import tempfile
import os
from shell_factory import exec_cmd
from shell.docker_file import DockerFile
from shell.bash_script import BashScript
from system_info import get_operating_system
from tempdir import TempDir


def test_exec_cmd():
    with TempDir():
        _, res = exec_cmd("ls", throw=False)
        assert res == 0


def test_unix_docker():
    if get_operating_system()!="windows":
        with TempDir():
            _, res = exec_cmd("sudo systemctl start docker", throw=False)
            bash_script = BashScript(content="ls")
            bash_script.append_env("PATH", "/root")
            docker_file = DockerFile(
                from_image="ubuntu:latest",
                script=bash_script)
            docker_file.throw_on_failure = False
            _, res = docker_file.build(result_image="test_img")
            assert res == 0
