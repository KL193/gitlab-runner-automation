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