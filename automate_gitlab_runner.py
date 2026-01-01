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



def register_runner(gitlab_url, token, executor):
    """Register the runner locally on the server."""
    print("Registering runner locally...")
    cmd = (
        f"sudo gitlab-runner register --non-interactive "
        f'--url "{gitlab_url}" '
        f'--token "{token}" '
        f'--executor "{executor}" '
        f'--tls-ca-file="{CA_CERT_PATH}"'
    )
    run_command(cmd)



def verify_runner_online(gitlab_url, project_id, access_token, description):
    """Wait and verify the runner is online via API."""
    print("Waiting for runner to come online (40 seconds)...")
    time.sleep(40)
    url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_id}/runners"
    response = requests.get(url, headers={"PRIVATE-TOKEN": access_token}, verify=CA_CERT_PATH)
    response.raise_for_status()
    for runner in response.json():
        if runner["description"] == description:
            if runner["online"]:
                print(f" Runner '{description}' is ONLINE and ready!")
                return
            else:
                print(f" Runner registered but not online yet. Status: {runner['status']}")
                return
    raise Exception("Runner not found in project runners list.")



def main():
    parser = argparse.ArgumentParser(
        description="Automate GitLab Runner setup using only the project URL"
    )
    parser.add_argument("--project-url", required=True,
                        help="Full GitLab project URL, e.g., https://gitlab.vizuamatix.com:6009/hnb-irr/demo1")
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION,
                        help=f"Runner name in UI (default: '{DEFAULT_DESCRIPTION}')")
    parser.add_argument("--tags", default=DEFAULT_TAGS,
                        help="Comma-separated tags, e.g., demo_runner,backend")
    parser.add_argument("--executor", default=DEFAULT_EXECUTOR,
                        choices=["shell", "docker"], help="Executor type (default: shell)")
    parser.add_argument("--version", default=DEFAULT_VERSION,
                        help=f"GitLab Runner version (default: {DEFAULT_VERSION})")

    args = parser.parse_args()


    # === Get access token from environment variable (secure & simple) ===
    access_token = os.getenv("GITLAB_TOKEN")
    if not access_token:
        raise Exception(
            "No access token found!\n"
            "Set it once on the server:\n"
            "    export GITLAB_TOKEN=\"glpat-your-real-token-here\"\n"
            "Add to ~/.bashrc to make it permanent."
        )