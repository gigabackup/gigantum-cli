import pytest
from unittest import mock

from docker.errors import ImageNotFound
import getpass
import click
from click.testing import CliRunner

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.commands.update import update
from gigantumcli.tests.fixtures import fixture_temp_work_dir, fixture_remove_client


class TestUpdate(object):
    def test_update(self, fixture_remove_client):
        runner = CliRunner()
        docker_obj = DockerInterface()

        # image should exist not exist before install
        try:
            # Check to see if the image has already been pulled
            docker_obj.client.images.get('gigantum/labmanager:latest')
            assert "Image should not exist"
        except ImageNotFound:
            pass

        # Pull old image
        old_tag = "55f05c26"
        docker_obj.client.images.pull("gigantum/labmanager", old_tag)
        docker_obj.client.api.tag('{}:{}'.format("gigantum/labmanager", old_tag), "gigantum/labmanager", 'latest')

        result = runner.invoke(update, ['-y'])
        assert result.exit_code == 0
        assert "Successfully pulled" in result.output

        # Latest should be a new image
        current_image = docker_obj.client.images.get("{}:latest".format("gigantum/labmanager"))
        short_id = current_image.short_id.split(':')[1]
        print(short_id)
        assert old_tag != short_id

