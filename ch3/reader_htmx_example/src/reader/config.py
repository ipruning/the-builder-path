"""
## ChangeLog
"""

import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Dict

import logfire
import yaml


def get_logfire_token() -> str:
    logfire_token = os.environ.get("LOGFIRE_TOKEN")
    if not logfire_token:
        raise ValueError("LOGFIRE_TOKEN is not set")
    return logfire_token


def get_env() -> str:
    env = os.getenv("ENV")
    if not env:
        env = "dev"
        logfire.warn(f"ENV is not set - falling back to {env}")
    return env


def get_service_name() -> str:
    config_path = Path.cwd() / "config" / "deploy.yml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
        service = config.get("service", "demo")
        if service == "demo":
            logfire.warn(f"SERVICE_NAME is not set - falling back to {service}")
        return service


def get_commit_id() -> str:
    commit_id = os.getenv("BUILD_COMMIT")
    if not commit_id:
        try:
            commit_id = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise ValueError("BUILD_COMMIT is not set")
    return commit_id


def get_system_info() -> Dict[str, str]:
    return {
        "commit_id": get_commit_id(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "os": platform.system(),
        "python_version": platform.python_version(),
    }


def configure_logfire() -> None:
    token = get_logfire_token()
    logfire.configure(token=token, service_name="bootstrap")

    env = get_env()
    service_name = get_service_name()
    commit_id = get_commit_id()

    logfire.configure(token=token, service_name=service_name, service_version=f"{commit_id}-{env}")
