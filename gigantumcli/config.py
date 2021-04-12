import yaml
import os
import click

DEFAULT_CONFIG_FILE = """
core:
  # Should the demo project import automatically on first log in? 
  import_demo_on_first_login: true
  # Default server will be automatically configured on first boot
  default_server: "https://gigantum.com"

# Project Container Configuration
# These limits are set on each individual Project container.
container:
  # If null, no limit
  # To set enter string with a units identification char (e.g. 100000b, 1000k, 128m, 1g)
  memory: null

  # If null, no limit
  # To set enter a float for the CPU allocation desired. e.g. 4 CPUs available, 1.5 limits container to 1.5 CPUs
  cpu: null

  # If null, do not set shared memory parameter when launching project container
  # To set enter string with a units identification char (e.g. 100000b, 1000k, 128m, 1g)
  # This parameter is only set when a Project is GPU enabled and being launched with nvidia docker runtime
  gpu_shared_mem: 2G

# Authentication Configuration
auth:
  # You *must* set to `browser` for multi-tenant mode
  identity_manager: local

# Environment Management Configuration
# URLs can specify a non-default branch using the format <url>@<branch>
# You can replace gigantum default bases or augment by adding your own repository here
environment:
  repo_url:
    - "https://github.com/gigantum/base-images.git"

"""


class ConfigOverrideFile:
    def __init__(self, working_dir: str) -> None:
        self.working_dir = os.path.expanduser(working_dir)
        self.config_file = os.path.join(self.working_dir, '.labmanager', 'config.yaml')

    def config_exists(self) -> bool:
        """Function to check if the config override file exists

        Returns:
            bool
        """
        return os.path.isfile(self.config_file)

    def is_browser_middleware_selected(self) -> bool:
        """Function to check if the browser middleware has been selected

        Returns:
            bool
        """
        if not self.config_exists():
            return False

        with open(self.config_file, 'rt') as cf:
            data = yaml.safe_load(cf)

        if data.get("auth"):
            if data["auth"].get("identity_manager") == "browser":
                return True

        return False

    def set_auth_middleware_mode(self, mode: str) -> None:
        """Method to set a server into "multi-tenant" mode by ensuring the middleware is set to browser

        Returns:
            None
        """
        if mode not in ['local', 'browser', 'anon_review']:
            raise click.UsageError("Unsupported auth mode: {}".format(mode))

        if not self.config_exists():
            self.write_default_config_override()

        with open(self.config_file, 'rt') as cf:
            data = yaml.safe_load(cf)

        if data.get("auth"):
            data["auth"]["identity_manager"] = mode
        else:
            data["auth"] = {"identity_manager": mode}

        with open(self.config_file, 'wt') as cf:
            yaml.safe_dump(data, cf)

    def write_default_config_override(self) -> None:
        """Writes the default config override file for managing the client as multi-tenant service

        Returns:

        """
        dst_dir = os.path.dirname(self.config_file)
        os.makedirs(dst_dir, exist_ok=True)
        with open(self.config_file, 'wt') as cf:
            cf.write(DEFAULT_CONFIG_FILE)
