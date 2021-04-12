from urllib.parse import urljoin, urlparse
import os
import json
import glob
import requests
from gigantumcli.utilities import ask_question
import urllib3
import shutil
import click


class ServerConfig:
    def __init__(self, working_dir):
        self.working_dir = os.path.expanduser(working_dir)
        self.servers_dir = os.path.join(self.working_dir, '.labmanager', 'servers')

    @staticmethod
    def _fetch_wellknown_data(url):
        succeed = False
        data = None
        verify = True
        try:
            response = requests.get(url, verify=verify)
            if response.status_code == 200:
                try:
                    # If a 200, make sure you get valid JSON back in case you were routed to some other 200 response.
                    data = response.json()
                    succeed = True
                except json.JSONDecodeError:
                    pass
        except requests.exceptions.SSLError:
            print("WARNING: SSL verification failed while trying to configure from server located at {}.\nIf this"
                  " is expected, it may be safe to proceed (e.g. a server created with a self-signed TLS "
                  "certificate).".format(url))
            if ask_question("Do you want to continue?"):
                # Try again with SSL verification disabled
                try:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    verify = False
                    response = requests.get(url, verify=verify)
                    if response.status_code == 200:
                        try:
                            # If a 200, make sure you get valid JSON back in case you were routed to some
                            # other 200 response.
                            data = response.json()
                            succeed = True
                        except json.JSONDecodeError:
                            pass
                except requests.exceptions.ConnectionError:
                    pass
            else:
                # User decided not to proceed.
                click.echo("SSL Verification failed on server located at {}.".format(url))
                raise click.Abort()
        except requests.exceptions.ConnectionError:
            pass

        return succeed, data, verify

    def _discover_server(self, url: str):
        """Method to load the server's discovery data

        Args:
            url(str): URL/domain to the server's root (users may not be precise here, so we'll try to be smart)

        Returns:
            dict: discovery data returned from the server
        """
        url_parts = urlparse(url)
        if not url_parts.scheme:
            url_parts = urlparse("https://" + url)

        team_url = urljoin("https://" + url_parts.netloc, 'gigantum/.well-known/discover.json')
        enterprise_url = urljoin("https://" + url_parts.netloc, '.well-known/discover.json')

        succeed, data, verify = self._fetch_wellknown_data(team_url)
        if not succeed:
            succeed, data, verify = self._fetch_wellknown_data(enterprise_url)

        if not succeed:
            raise click.UsageError("Failed to discover configuration for server located at"
                                   " `{}`. Check server URL and try again.".format(url))
        return data, verify

    def add_server(self, url):
        """Method to discover a server's configuration and add it to the local configured servers

        Args:
            url: URL/domain to the server's root (users may not be precise here, so we'll try to be smart)

        Returns:
            str: id for the server
        """
        server_data, verify = self._discover_server(url)

        # Ensure core URLS have trailing slashes to standardize within codebase
        server_data['git_url'] = server_data['git_url'] if server_data['git_url'][-1] == '/' \
            else server_data['git_url'] + '/'
        server_data['hub_api_url'] = server_data['hub_api_url'] if server_data['hub_api_url'][-1] == '/' \
            else server_data['hub_api_url'] + '/'
        server_data['object_service_url'] = server_data['object_service_url'] \
            if server_data['object_service_url'][-1] == '/' \
            else server_data['object_service_url'] + '/'

        # Verify Server is not already configured
        server_data_file = os.path.join(self.servers_dir, server_data['id'] + ".json")
        if os.path.exists(server_data_file):
            raise ValueError("The server `{}` located at {} is already configured.".format(server_data['name'], url))

        # Fetch Auth configuration
        response = requests.get(server_data['auth_config_url'], verify=verify)
        if response.status_code != 200:
            raise click.UsageError("Failed to load auth configuration "
                                   "for server located at {}: {}".format(url, response.status_code))
        auth_data = response.json()

        # Create servers dir if it is missing (maybe this user has never started the client)
        if not os.path.isdir(self.servers_dir):
            os.makedirs(self.servers_dir, exist_ok=True)

        # Save configuration data
        save_data = {"server": server_data,
                     "auth": auth_data}
        with open(server_data_file, 'wt') as f:
            json.dump(save_data, f, indent=2)

        # Create directory for server's projects/datasets
        user_storage_dir = os.path.join(self.working_dir, 'servers', server_data['id'])
        os.makedirs(user_storage_dir, exist_ok=True)

        return server_data['id']

    def list_servers(self, should_print: bool = False):
        """Method to list configured servers, optionally printing a table

        Args:
            should_print(bool): flag indicating if the results should be printed

        Returns:
            list
        """
        configured_servers = list()
        id_len = 0
        name_len = 0
        url_len = 0
        for server_file in glob.glob(os.path.join(self.servers_dir, "*.json")):
            with open(server_file, 'rt') as f:
                data = json.load(f)
                hub_url_parts = urlparse(data['server']['hub_api_url'])
                server_url = hub_url_parts.scheme + "://" + hub_url_parts.netloc
                configured_servers.append((data['server']['id'], data['server']['name'], server_url))
                id_len = max(id_len, len(data['server']['id']))
                name_len = max(name_len, len(data['server']['name']))
                url_len = max(url_len, len(server_url))

        if should_print:
            id_len += 5
            name_len += 5
            url_len += 5

            print("Server ID".ljust(id_len), "Server Name".ljust(name_len), "Server Location".ljust(url_len))
            for server in configured_servers:
                print(server[0].ljust(id_len), server[1].ljust(name_len), server[2].ljust(url_len))
            print("\n")

        return configured_servers

    def remove_server(self, server_id: str) -> None:
        """Method to remove a server

        Args:
            server_id(str): ID of the server to remove

        Returns:
            None
        """
        # Set CURRENT to a reasonable value if it is set to the server being removed
        current_path = os.path.join(self.servers_dir, 'CURRENT')
        with open(current_path, 'rt') as cf:
            current_server = cf.read()

        if current_server == server_id:
            new_current_server = None
            servers = self.list_servers()
            # Try gigantum-com first
            match = [s for s in servers if s[0] == "gigantum-com"]
            if match:
                new_current_server = "gigantum-com"
            else:
                other_servers = [s for s in servers if s[0] != server_id]
                if len(other_servers) == 0:
                    raise ValueError("You must have another valid server configured (e.g. gigantum.com) before "
                                     "removing this server")
                # Just pick the first one
                new_current_server = other_servers[0][0]

            with open(current_path, 'wt') as cf:
                cf.write(new_current_server)

        # Remove user data dir
        shutil.rmtree(os.path.join(self.working_dir, 'servers', server_id), ignore_errors=True)

        # Remove dataset file cache (if it exists)
        shutil.rmtree(os.path.join(self.working_dir, '.labmanager', 'datasets', server_id), ignore_errors=True)

        # Remove sensitive file cache (if it exists
        shutil.rmtree(os.path.join(self.working_dir, '.labmanager', 'secrets', server_id), ignore_errors=True)

        # Remove cached JWKS
        jwks_file = os.path.join(self.working_dir, '.labmanager', 'identity', "{}-jwks.json".format(server_id))
        if os.path.isfile(jwks_file):
            os.remove(jwks_file)

        # Remove server configuration
        os.remove(os.path.join(self.servers_dir,  "{}.json".format(server_id)))
