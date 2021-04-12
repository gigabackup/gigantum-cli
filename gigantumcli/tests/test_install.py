from docker.errors import ImageNotFound
from click.testing import CliRunner

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.commands.install import install
from gigantumcli.tests.fixtures import fixture_temp_work_dir, fixture_remove_client


class TestInstall(object):
    def test_install(self, fixture_remove_client):
        runner = CliRunner()
        docker_obj = DockerInterface()

        # image should exist not exist before install
        try:
            # Check to see if the image has already been pulled
            docker_obj.client.images.get('gigantum/labmanager:latest')
            assert "Image should not exist"
        except ImageNotFound:
            pass

        result = runner.invoke(install, [])
        assert result.exit_code == 0
        assert "Successfully pulled" in result.output

        # image should exist after install
        docker_obj = DockerInterface()
        docker_obj.client.images.get('gigantum/labmanager')

        # Calling again should exit with a message since already installed
        result = runner.invoke(install, [])
        assert result.exit_code == 2
        assert "image already installed" in result.output

