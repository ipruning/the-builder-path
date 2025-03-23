import subprocess
from pathlib import Path

import modal

APP_NAME = Path(__file__).stem

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install("pip==25.0.1")
    .pip_install("comfy-cli==1.3.8")
    .run_commands("comfy --skip-prompt install --nvidia --version 0.3.26")
)


def hf_download():
    from huggingface_hub import hf_hub_download

    flux_model = hf_hub_download(
        repo_id="Comfy-Org/flux1-schnell",
        filename="flux1-schnell-fp8.safetensors",
        cache_dir="/cache",
    )

    subprocess.run(
        f"ln -s {flux_model} /root/comfy/ComfyUI/models/checkpoints/flux1-schnell-fp8.safetensors",
        shell=True,
        check=True,
    )


vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)

image = (
    image.pip_install("huggingface_hub[hf_transfer]==0.29.3")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        hf_download,
        volumes={"/cache": vol},
    )
)

image = image.add_local_file(
    Path(__file__).parent / "workflow_api.json", "/root/workflow_api.json"
)

app = modal.App(
    name=APP_NAME,
    image=image,
)


@app.function(
    allow_concurrent_inputs=10,
    max_containers=1,
    gpu="L40S",
    volumes={"/cache": vol},
)
@modal.web_server(8000, startup_timeout=60)
def ui():
    subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)
