# gitlab-runner-automation

# GitLab Runner Automation

Python tool to fully automate the installation, registration, and configuration of GitLab Runners on self-hosted GitLab instances — including handling self-signed certificates.

## Why this tool?
Manual GitLab Runner setup is repetitive and error-prone (especially with self-signed certs and new authentication tokens).  
This script reduces the process from ~20–30 minutes to ~3 minutes per runner.

## Features
- Installs specific GitLab Runner version (default: 16.11.0)
- Places self-signed CA certificate automatically
- Uses GitLab API to create runner and get token (no manual copy-paste)
- Registers runner with desired executor, description, and tags
- Verifies runner is online
- Idempotent: safe to run multiple times

## Requirements
- Python 3.8+
- GitLab access token with `api` and `create_runner` scopes
- Self-signed CA certificate file

## Installation
```bash
git clone https://github.com/YOUR_USERNAME/gitlab-runner-automation.git
cd gitlab-runner-automation
pip install -r requirements.txt
