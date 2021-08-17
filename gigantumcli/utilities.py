from __future__ import print_function
from six.moves import input
from typing import Optional, Tuple
import ctypes
import os
import platform
import subprocess
import shlex
import re
import click


def ask_question(question, accept_confirmation=False):
    """Method to ask the user a yes/no question

    Args:
        question(str): A question to ask the user
        accept_confirmation(bool): Optional flag, if True will automatically accept question

    Returns:
        bool: True if yes, False if no
    """
    if accept_confirmation:
        return True

    valid_response = {"yes": True, "y": True, "no": False, "n": False}

    while True:
        print("{} [y/n]: ".format(question), end="")
        choice = input().lower().strip()
        if choice in valid_response:
            return valid_response[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def is_running_as_admin():
    """Method to check if the python script is running as an administrator

    Returns:
        bool
    """
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()

    return is_admin


def get_nvidia_gpu_info() -> Tuple[Optional[str], int]:
    """Method to get the driver version and number of GPUs available

    Notes:
        - If drivers aren't installed, the driver version is set to None
        - If the driver version has major.minor.revision, only major.minor is returned

    Returns:
        driver version, number of GPUs
    """
    driver_version = None
    num_gpus = 0
    if platform.system() == 'Linux':
        try:
            bash_command = "nvidia-smi --query-gpu=driver_version --format=csv,noheader"
            process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            if not error:
                m = re.findall(r"([\d.]+)", output.decode())
                if m:
                    driver_version = m[0]

                if driver_version is None:
                    # Failed to match on the regex, so there's a possible issue with drivers
                    click.echo()
                    click.echo()
                    click.secho('********* WARNING *********', bg='yellow', bold=True)
                    click.echo()
                    click.echo(f"Failed to get NVIDIA driver version due to error: {output.decode()}")
                    click.echo(f"GPU support is disabled.")
                    if "driver/library version mismatch" in output.decode().lower():
                        click.echo()
                        click.echo(f"It is likely that rebooting this system will resolve the issue.")
                    click.echo()
                    click.secho('********* WARNING *********', bg='yellow', bold=True)
                    click.echo()
                    click.echo()
                    return driver_version, num_gpus

                # If driver has a build version, strip it because we don't match on that.
                parts = driver_version.split('.')
                driver_version = f"{parts[0]}.{parts[1]}"
                num_gpus = len(m)

        except FileNotFoundError:
            pass
    return driver_version, num_gpus


def get_nvidia_smi_path() -> Optional[str]:
    """Function to look for the nvidia-smi binary

    This is then provided to the Client and is used when launching GPU enabled projects with the "new" Docker
    launch configuration that does not use the nvidia runtime.

    Returns:
        absolute path to the nvidia-smi binary if it exists.
    """
    nvidia_smi_path = None
    if platform.system() == 'Linux':
        try:
            process = subprocess.Popen(['which', 'nvidia-smi'], stdout=subprocess.PIPE)
            output, error = process.communicate()
            if not error:
                result = output.decode().strip()
                if result.endswith('nvidia-smi'):
                    nvidia_smi_path = result
        except:
            # If we can't find nvidia-smi just continue on
            pass

    return nvidia_smi_path
