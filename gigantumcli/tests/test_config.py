from click.testing import CliRunner
import os
import yaml
import pytest

from gigantumcli.tests.fixtures import fixture_temp_work_dir
from gigantumcli.commands.config import config


class TestConfig(object):
    def test_init_fresh_workdir(self, fixture_temp_work_dir):
        runner = CliRunner()

        result = runner.invoke(config, ['init', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Config file written" in result.output

    def test_init(self, fixture_temp_work_dir):
        runner = CliRunner()

        dst_dir = os.path.dirname(os.path.join(fixture_temp_work_dir, '.labmanager'))
        os.makedirs(dst_dir, exist_ok=True)
        result = runner.invoke(config, ['init', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Config file written" in result.output

    def test_init_exists(self, fixture_temp_work_dir):
        runner = CliRunner()

        result = runner.invoke(config, ['init', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Config file written" in result.output

        result = runner.invoke(config, ['init', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 1
        assert "A config file already exists" in result.output

    def test_set_mode(self, fixture_temp_work_dir):
        def get_mode() -> str:
            with open(os.path.join(fixture_temp_work_dir, '.labmanager', 'config.yaml'), 'rt') as cf:
                data = yaml.safe_load(cf)
                return data["auth"]["identity_manager"]

        runner = CliRunner()

        result = runner.invoke(config, ['set-auth-mode', 'local', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Config updated." in result.output
        assert get_mode() == "local"

        result = runner.invoke(config, ['set-auth-mode', 'multi-user', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Config updated." in result.output
        assert get_mode() == "browser"

        result = runner.invoke(config, ['set-auth-mode', 'local', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 0
        assert "Config updated." in result.output
        assert get_mode() == "local"

        result = runner.invoke(config, ['set-auth-mode', 'fake', '--working-dir', fixture_temp_work_dir])
        assert result.exit_code == 2
        assert "invalid choice: fake." in result.output
        assert get_mode() == "local"
