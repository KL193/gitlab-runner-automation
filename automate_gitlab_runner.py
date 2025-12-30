import argparse
import json
import os
import subprocess
import time
import urllib.parse
import requests

def run_command(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if check and result.returncode != 0:
        raise Exception(f"Failed: {cmd}\nError: {result.stderr}")
    return result.stdout.strip()

def get_installed_version():
    try:
        output = run_command("/usr/bin/gitlab-runner --version", check=False)
        for line in output.splitlines():
            if "Version:" in line:
                return line.split()[1]
        return None
    except:
        return None

def install_runner(version):
    installed = get_installed_version()
    if installed == version:
        print(f"GitLab Runner {version} already installed. Skipping install.")
        return
    print(f"Installing GitLab Runner {version}")
    run_command('curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash')
    run_command("sudo apt update")
    run_command(f"sudo apt install -y gitlab-runner={version}-1")


def get_project_id(gitlab_url, project_path, access_token, ca_cert):
    encoded_path = urllib.parse.quote_plus(project_path)
    url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{encoded_path}"
    response = requests.get(url, headers={"PRIVATE-TOKEN": access_token}, verify=ca_cert)
    response.raise_for_status()
    return response.json()["id"]


def create_runner_via_api(gitlab_url, project_id, access_token, ca_cert, description, tags):
    url = f"{gitlab_url.rstrip('/')}/api/v4/user/runners"
    payload = {
        "runner_type": "project_type",
        "project_id": project_id,
        "description": description,
        "tag_list": [tag.strip() for tag in tags.split(",")] if tags else []
    }
    response = requests.post(url, headers={"PRIVATE-TOKEN": access_token}, json=payload, verify=ca_cert)
    response.raise_for_status()
    return response.json()["token"]


def register_runner(gitlab_url, token, executor, ca_file):
    print("Registering runner with GitLab...")
    cmd = (
        f"sudo gitlab-runner register --non-interactive "
        f'--url "{gitlab_url}" '
        f'--token "{token}" '
        f'--executor "{executor}" '
        f'--tls-ca-file="{ca_file}"'
    )
    run_command(cmd)


def verify_runner_online(gitlab_url, project_id, access_token, ca_cert, description):
    print("Waiting for runner to come online...")
    time.sleep(40)
    url = f"{gitlab_url.rstrip('/')}/api/v4/projects/{project_id}/runners"
    response = requests.get(url, headers={"PRIVATE-TOKEN": access_token}, verify=ca_cert)
    response.raise_for_status()
    for runner in response.json():
        if runner["description"] == description:
            if runner["online"]:
                print(f"✅ Runner '{description}' is ONLINE and ready!")
                return
            else:
                print(f"⚠️  Runner registered but not online yet. Status: {runner['status']}")
                return
    raise Exception("Runner not found in project runners list.")