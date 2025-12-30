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