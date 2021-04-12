import pytest
import tempfile
import uuid
import os
import shutil
import responses
import click

from gigantumcli.server import ServerConfig


@pytest.fixture
def server_config():
    """Fixture to create a Build instance with a test image name that does not exist and cleanup after"""
    unit_test_working_dir = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
    os.mkdir(unit_test_working_dir)
    os.makedirs(os.path.join(unit_test_working_dir, '.labmanager', 'identity'))
    yield ServerConfig(working_dir=unit_test_working_dir)
    shutil.rmtree(unit_test_working_dir)


class TestServerConfig(object):
    @responses.activate
    def test_server_discovery_fails(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={},
                      status=404)
        responses.add(responses.GET, 'https://test2.gigantum.com/.well-known/discover.json',
                      json={},
                      status=404)

        with pytest.raises(click.UsageError):
            server_config.add_server("test2.gigantum.com")

    @responses.activate
    def test_auth_discovery_fails(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={},
                      status=404)
        responses.add(responses.GET, 'https://test2.gigantum.com/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/.well-known/auth.json',
                      json={},
                      status=404)

        with pytest.raises(click.UsageError):
            server_config.add_server("https://test2.gigantum.com/")

        with pytest.raises(click.UsageError):
            server_config.add_server("https://thiswillneverwork.gigantum.com/")

    @responses.activate
    def test_add_server(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test2.api.gigantum.io",
                            "issuer": "https://test2-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test2-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test2.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)

        server_id = server_config.add_server("https://test2.gigantum.com/")
        assert server_id == 'another-server'
        assert os.path.isfile(os.path.join(server_config.servers_dir, 'another-server.json'))
        assert os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'another-server'))

    @responses.activate
    def test_add_server_already_configured(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test2.api.gigantum.io",
                            "issuer": "https://test2-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test2-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test2.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        server_id = server_config.add_server("https://test2.gigantum.com/")
        assert server_id == 'another-server'
        assert os.path.isfile(os.path.join(server_config.servers_dir, 'another-server.json'))
        assert os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'another-server'))

        with pytest.raises(ValueError):
            server_config.add_server("https://test2.gigantum.com/")

    @responses.activate
    def test_list_servers(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test2.api.gigantum.io",
                            "issuer": "https://test2-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test2-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test2.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)
        responses.add(responses.GET, 'https://test3.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'my-server',
                            "name": "My Server 1",
                            "git_url": "https://test3.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test3.gigantum.com/api/v1/",
                            "object_service_url": "https://test3.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search3.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test3.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test3.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test3.api.gigantum.io",
                            "issuer": "https://test3-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test3-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test3.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)

        server_id = server_config.add_server("https://test2.gigantum.com/")
        assert server_id == 'another-server'
        assert os.path.isfile(os.path.join(server_config.servers_dir, 'another-server.json'))
        assert os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'another-server'))
        server_id = server_config.add_server("https://test3.gigantum.com/")
        assert server_id == 'my-server'
        assert os.path.isfile(os.path.join(server_config.servers_dir, 'my-server.json'))
        assert os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'my-server'))

        server_list = server_config.list_servers(should_print=True)

        assert len(server_list) == 2

    @responses.activate
    def test_remove_server_only_one(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test2.api.gigantum.io",
                            "issuer": "https://test2-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test2-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test2.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)

        server_id = server_config.add_server("https://test2.gigantum.com/")
        os.makedirs(os.path.join(server_config.working_dir, '.labmanager', 'servers'), exist_ok=True)
        with open(os.path.join(server_config.working_dir, '.labmanager', 'servers', 'CURRENT'), 'wt') as cf:
            cf.write("another-server")

        assert server_id == 'another-server'
        assert os.path.isfile(os.path.join(server_config.servers_dir, 'another-server.json'))
        assert os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'another-server'))

        with pytest.raises(ValueError):
            server_config.remove_server('another-server')

    @responses.activate
    def test_remove_server(self, server_config):
        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'another-server',
                            "name": "Another server",
                            "git_url": "https://test2.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test2.gigantum.com/api/v1/",
                            "object_service_url": "https://test2.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search2.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test2.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test2.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test2.api.gigantum.io",
                            "issuer": "https://test2-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test2-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test2.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)
        responses.add(responses.GET, 'https://test3.gigantum.com/gigantum/.well-known/discover.json',
                      json={"id": 'my-server',
                            "name": "My Server 1",
                            "git_url": "https://test3.repo.gigantum.com/",
                            "git_server_type": "gitlab",
                            "hub_api_url": "https://test3.gigantum.com/api/v1/",
                            "object_service_url": "https://test3.api.gigantum.com/object-v1/",
                            "user_search_url": "https://user-search3.us-east-1.cloudsearch.amazonaws.com",
                            "lfs_enabled": True,
                            "auth_config_url": "https://test3.gigantum.com/gigantum/.well-known/auth.json"},
                      status=200)

        responses.add(responses.GET, 'https://test3.gigantum.com/gigantum/.well-known/auth.json',
                      json={"audience": "test3.api.gigantum.io",
                            "issuer": "https://test3-auth.gigantum.com",
                            "signing_algorithm": "RS256",
                            "public_key_url": "https://test3-auth.gigantum.com/.well-known/jwks.json",
                            "login_url": "https://test3.gigantum.com/client/login",
                            "login_type": "auth0",
                            "auth0_client_id": "0000000000000000"},
                      status=200)

        server_id = server_config.add_server("https://test2.gigantum.com/")
        assert server_id == 'another-server'
        server_id = server_config.add_server("https://test3.gigantum.com/")
        assert server_id == 'my-server'

        # mock some more stuff
        server_file = os.path.join(server_config.servers_dir,  "another-server.json")
        with open(os.path.join(server_config.servers_dir, 'CURRENT'), 'wt') as cf:
            cf.write("another-server")

        cached_jwks = os.path.join(server_config.working_dir, '.labmanager', 'identity',
                               'another-server-jwks.json')
        with open(cached_jwks, 'wt') as jf:
            jf.write("FAKE DATA")

        test_user_data = os.path.join(server_config.working_dir, 'servers', 'another-server',
                               'TEST_FILE')
        with open(test_user_data, 'wt') as jf:
            jf.write("FAKE DATA")

        assert os.path.isfile(test_user_data)
        assert os.path.isfile(cached_jwks)
        assert os.path.isfile(server_file)
        assert os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'another-server'))

        server_config.remove_server('another-server')

        assert not os.path.isfile(test_user_data)
        assert not os.path.isfile(cached_jwks)
        assert not os.path.isfile(server_file)
        assert not os.path.isdir(os.path.join(server_config.working_dir, 'servers', 'another-server'))

        current_path = os.path.join(server_config.servers_dir, 'CURRENT')
        with open(current_path, 'rt') as cf:
            assert cf.read() == 'my-server'
