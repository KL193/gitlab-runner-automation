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


def extract_gitlab_info(project_url):
    """Extract GitLab base URL and project path from full project URL."""
    parsed = urllib.parse.urlparse(project_url)
    gitlab_url = f"{parsed.scheme}://{parsed.netloc}"
    project_path = parsed.path.lstrip('/')
    if project_path.endswith('.git'):
        project_path = project_path[:-4]
    return gitlab_url, project_path



def get_project_id(gitlab_url, project_path, access_token):
    """Get internal project ID using GitLab API."""
    encoded_path = urllib.parse.quote_plus(project_path)
    url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{encoded_path}"
    response = requests.get(url, headers={"PRIVATE-TOKEN": access_token}, verify=CA_CERT_PATH)
    response.raise_for_status()
    return response.json()["id"]


def create_runner_via_api(gitlab_url, project_id, access_token, description, tags):
    """Create project-specific runner via API and return registration token."""
    url = f"{gitlab_url.rstrip('/')}/api/v4/user/runners"
    payload = {
        "runner_type": "project_type",
        "project_id": project_id,
        "description": description,
        "tag_list": [tag.strip() for tag in tags.split(",")] if tags else []
    }
    response = requests.post(url, headers={"PRIVATE-TOKEN": access_token}, json=payload, verify=CA_CERT_PATH)
    response.raise_for_status()
    return response.json()["token"]
