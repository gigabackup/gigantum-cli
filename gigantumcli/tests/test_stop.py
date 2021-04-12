from click.testing import CliRunner

from gigantumcli.dockerinterface import DockerInterface
from gigantumcli.commands.stop import stop
from gigantumcli.tests.test_cleanup_containers import fixture_create_dummy_containers


class TestStop:
    def test_stop_auto_confirm(self, fixture_create_dummy_containers):
        runner = CliRunner()
        result = runner.invoke(stop, ['-y'])
        assert result.exit_code == 0
        assert result.output == """- Cleaning up container for Project: test-project-2
- Cleaning up container for Project: test-project
- Cleaning up Gigantum Client container
- Cleaning up Gigantum Client container
"""

        docker_obj = DockerInterface()
        running_containers = docker_obj.client.containers.list()
        assert len(running_containers) == 1
        assert running_containers[0].name == 'rando'
