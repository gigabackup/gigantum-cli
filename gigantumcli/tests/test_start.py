import pytest
from unittest import mock

from docker.errors import ImageNotFound
import getpass
import click
from click.testing import CliRunner
from gigantumcli.commands.start import start

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.tests.fixtures import fixture_temp_work_dir, fixture_remove_client


def mock_api_check(launch_browser, timeout):
    return launch_browser


class TestStart(object):
    def test_is_running_as_admin(self):
        from gigantumcli.utilities import is_running_as_admin
        assert is_running_as_admin() is False

    def test_start(self, fixture_temp_work_dir):
        runner = CliRunner()

        result = runner.invoke(start, ['-y', '-w', 60, '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Starting, please wait" in result.output
        assert "Client running on http://localhost:10000" in result.output

        docker = DockerInterface()

        is_running = False
        for container in docker.client.containers.list():
            if container.name in 'gigantum.labmanager':
                is_running = True
                break

        assert is_running is True

    def test_start_block_external(self, fixture_temp_work_dir):
        runner = CliRunner()

        result = runner.invoke(start, ['-y', '-w', 60, '--external', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 1
        assert "WARNING: When running the Client" in result.output

        docker = DockerInterface()

        is_running = False
        for container in docker.client.containers.list():
            if container.name in 'gigantum.labmanager':
                is_running = True
                break

        assert is_running is False

    def test_start_different_port(self, fixture_temp_work_dir):
        runner = CliRunner()

        result = runner.invoke(start, ['-y', '-w', 60, '--port', 20000, '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Starting, please wait" in result.output
        assert "Client running on http://localhost:20000" in result.output

        docker = DockerInterface()

        is_running = False
        for container in docker.client.containers.list():
            if container.name in 'gigantum.labmanager':
                is_running = True
                break

        assert is_running is True
