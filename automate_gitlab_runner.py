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

