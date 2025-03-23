import secrets
import subprocess
import time
from pathlib import Path

import modal

MARIMO_NOTEBOOK_PATH = Path(__file__).parent / "notebook.py"

APP_NAME = Path(__file__).stem

app = modal.App(
    name=APP_NAME,
    image=modal.Image.debian_slim()
    .pip_install("uv")
    .add_local_file(MARIMO_NOTEBOOK_PATH, remote_path="/root/notebook.py"),
)

TOKEN = secrets.token_urlsafe(16)
PORT = 2718


@app.function(max_containers=1, timeout=1_500, gpu="H100")  # L40S
def run_marimo(timeout: int):
    with modal.forward(PORT) as tunnel:
        marimo_process = subprocess.Popen(
            [
                "uvx",
                "marimo",
                "edit",
                "--headless",
                "--host",
                "0.0.0.0",
                "--port",
                str(PORT),
                "--token-password",
                TOKEN,
                "/root/notebook.py",
            ],
        )

        print(f"Marimo available at => {tunnel.url}?access_token={TOKEN}")

        try:
            end_time = time.time() + timeout
            while time.time() < end_time:
                time.sleep(5)
            print(f"Reached end of {timeout} second timeout period. Exiting...")
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            marimo_process.kill()


@app.local_entrypoint()
def main():
    run_marimo.remote(1000)
