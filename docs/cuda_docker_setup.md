# Agent Zero: CUDA GPU Support 🚀

Run Agent Zero with NVIDIA GPU acceleration. The CUDA image is a **thin overlay on the regular run image**: only `torch`/`torchvision` (CPU → CUDA wheels) and `faiss-cpu` (→ `faiss-gpu-cu12`) are swapped, everything else is inherited unchanged. CUDA runtime libraries are bundled in the pip wheels and the driver is injected by the NVIDIA Container Toolkit, so no CUDA apt packages are installed.

What gets faster: local embeddings (`sentence-transformers`), Whisper speech-to-text, FAISS memory search. Remote LLM API calls are unaffected.

---

## Prerequisites

1. **NVIDIA GPU** (CUDA 12 capable) and a **driver ≥ 550** on the host
2. **NVIDIA Container Toolkit** ([install guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)) — verify with:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
   ```
3. **Docker Engine + Docker Compose v2** (`docker compose version`)

---

## 1. Build the CUDA image

From the `docker/run` directory:

```bash
docker compose -f docker-compose.cuda.yml build
```

Build args (pass with `--build-arg` or via env for compose):

| Arg | Default | Purpose |
|---|---|---|
| `BASE_IMAGE` / `BASE_TAG` | `frdel/agent-zero-run` / `latest` | run image to overlay (`A0_BASE_TAG=development` for compose) |
| `TORCH_INDEX_URL` | `.../whl/cu124` | use `.../whl/cu121` for older drivers |
| `TORCH_VERSION`, `TORCHVISION_VERSION`, `FAISS_GPU_VERSION` | pinned to base image | keep in sync with `requirements.txt` |

The build fails early if the installed torch is not a CUDA build or faiss lacks GPU support.

---

## 2. Run

```bash
docker compose -f docker-compose.cuda.yml up -d
```

Open [http://localhost:50080](http://localhost:50080).

Runtime knobs (environment variables, e.g. in a `.env` next to the compose file):

| Var | Default | Purpose |
|---|---|---|
| `A0_BIND` | `127.0.0.1` | set `0.0.0.0` to expose on the LAN (put auth in front first) |
| `A0_PORT` | `50080` | host port |
| `NVIDIA_VISIBLE_DEVICES` | `all` | e.g. `0` to pin one GPU |
| `NVIDIA_GPU_COUNT` | `all` | number of GPUs reserved |
| `A0_MEM_LIMIT` | `16g` | container RAM cap |

Safe-operation defaults baked into the compose file: `restart: unless-stopped`, `init`, 60 s stop grace, `/health` healthcheck, log rotation (5 × 20 MB), PID limit, localhost-only port binding.

---

## 3. Verify GPU is used

```bash
docker exec agent-zero-cuda nvidia-smi
docker exec agent-zero-cuda /opt/venv/bin/python -c "import torch,faiss;print(torch.cuda.is_available(), torch.cuda.get_device_name(0), faiss.get_num_gpus())"
docker inspect --format '{{.State.Health.Status}}' agent-zero-cuda   # healthy
```

---

## 4. Stop / switch CPU ↔ GPU

Both compose files mount the same `./agent-zero` data directory, so switching loses nothing.

```bash
docker compose -f docker-compose.cuda.yml down     # stop GPU
docker compose up -d                               # start CPU
```

---

## Troubleshooting

- **`could not select device driver "nvidia"`** → NVIDIA Container Toolkit missing or Docker not restarted after install (`sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`).
- **`torch.cuda.is_available()` is `False` inside the container** → driver too old for the wheel's CUDA version; rebuild with `--build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121`.
- **Container restarts in a loop** → `docker logs agent-zero-cuda`; the healthcheck only passes once the UI answers on `/health`, allow up to 2 min on first start (`start_period`).
- **OOM** → raise `A0_MEM_LIMIT`, or lower model sizes in Settings.

---

## More Information

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/)
- [PyTorch CUDA wheels](https://pytorch.org/get-started/locally/)
- [Agent Zero](https://github.com/frdel/agent-zero)
