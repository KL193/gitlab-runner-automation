import argparse
import json
import os
import subprocess
import time
import urllib.parse
import requests


CA_CERT_PATH = "/etc/gitlab-runner/certs/gitlab.vizuamatix.com.crt"

# Default values
DEFAULT_DESCRIPTION = "Automated Runner"
DEFAULT_TAGS = ""
DEFAULT_EXECUTOR = "shell"
DEFAULT_VERSION = "16.11.0"  # Change if needed (e.g., "18.0.1")

def run_command(cmd, check=True):
    """Run shell command and raise error if it fails."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if check and result.returncode != 0:
        raise Exception(f"Command failed: {cmd}\nError: {result.stderr.strip()}")
    return result.stdout.strip()


def get_installed_version():
    """Check current GitLab Runner version."""
    try:
        output = run_command("/usr/bin/gitlab-runner --version", check=False)
        for line in output.splitlines():
            if "Version:" in line:
                return line.split()[1]
        return None
    except:
        return None

def install_runner(version):
    """Install specific GitLab Runner version if not already present."""
    installed = get_installed_version()
    if installed == version:
        print(f"GitLab Runner {version} already installed. Skipping installation.")
        return
    print(f"Installing GitLab Runner {version}...")
    run_command('curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash')
    run_command("sudo apt update")
    run_command(f"sudo apt install -y gitlab-runner={version}-1")