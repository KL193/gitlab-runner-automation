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
    print(f"Installing GitLab Runner {version}...")
    run_command('curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash')
    run_command("sudo apt update")
    run_command(f"sudo apt install -y gitlab-runner={version}-1")