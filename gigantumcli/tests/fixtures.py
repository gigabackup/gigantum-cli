import pytest
from gigantumcli.dockerinterface import DockerInterface
from docker.errors import ImageNotFound
import os
import shutil
import time


@pytest.fixture()
def fixture_remove_client():

    """Fixture start fake project and client containers"""
    docker_obj = DockerInterface()
    try:
        # Check to see if the image has already been pulled
        img = docker_obj.client.images.get('gigantum/labmanager:latest')
        docker_obj.client.images.remove(img.id, force=True)
    except ImageNotFound:
        pass


@pytest.fixture()
def fixture_temp_work_dir():
    """Fixture create a temporary working directory"""
    temp_dir = os.path.join('/tmp', 'testing-working-dir')
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    yield temp_dir

    # Stop and remove Client container
    docker_obj = DockerInterface()
    time.sleep(.1)
    for container in docker_obj.client.containers.list(all=True):
        if container.name == "gigantum.labmanager":
            container.remove(force=True)
            time.sleep(.1)

    # Remove temp dir
    shutil.rmtree(temp_dir)
