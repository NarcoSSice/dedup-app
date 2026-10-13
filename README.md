# Image Duplicate Finder

A service that adds images to a vector store and finds their duplicates and near-duplicates: resized, compressed, cropped (up to ~20%), brightness/contrast-adjusted, slightly rotated or flipped, and watermarked copies. Images that only show the same thing (two different photos of the same coin) are not reported as duplicates.

Uploaded images are compared with each other and with every other image in the store. The service runs on CPU and comes with a web UI.

**Stack:** PyTorch (SSCD model), FastAPI, Qdrant, MongoDB, React + shadcn/ui, Docker Compose.

## Contents

- [Quick start (Docker)](#quick-start-docker)
- [Running locally](#running-locally)
- [Tests](#tests)
- [Configuration](#configuration)
- [API](#api)
- [Architecture](#architecture)
- [Why this model, store and threshold](#why-this-model-store-and-threshold)
- [Deviations from the task](#deviations-from-the-task)
- [Known limitations and possible improvements](#known-limitations-and-possible-improvements)

## Quick start (Docker)

```bash
docker compose up --build
```

| What | URL |
|---|---|
| Web UI | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |

The first build downloads the CPU-only PyTorch wheels and the SSCD weights (~100 MB), so it takes a few minutes. Data lives in Docker volumes and survives restarts; `docker compose down -v` wipes it.

Settings can be overridden from the shell or a `.env` file next to `docker-compose.yml`:

```bash
DUPLICATE_THRESHOLD=0.85 docker compose up
```

Embedding is the slow part, so it runs in separate worker processes. To process uploads faster, add workers (keep `TORCH_THREADS × workers` within the number of CPU cores):

```bash
docker compose up --scale worker=3
```

## Running locally

Requirements: Python 3.11–3.12 with [Poetry](https://python-poetry.org/), Node.js 22+, Docker (for MongoDB and Qdrant).

**1. Databases.** Start only MongoDB and Qdrant from the compose file. Both are published on `127.0.0.1`:

```bash
docker compose up -d mongo qdrant
```

**2. Backend.** Run the API and at least one worker, each in its own terminal, from `backend/`:

```bash
cd backend
cp .env.sample .env      # defaults point at localhost
poetry install
poetry run python app/main.py      # API on http://localhost:8000
poetry run python app/worker.py    # embedding worker
```

On first start the worker downloads the SSCD weights to `backend/dedup_model/`. Uploaded files are stored in `backend/data/images/`.

**3. Frontend.** From `frontend/`:

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, /api is proxied to localhost:8000
```

## Tests

The backend tests use a separate, throwaway MongoDB (port 27018, data in tmpfs) so they never touch the app database. Qdrant runs in-process in memory. The tests use the real SSCD model, which is downloaded on the first run.

```bash
docker compose -f docker-compose.test.yml up -d --wait
cd backend && poetry run pytest
```

What they cover (`backend/tests/`):

- successful upload, and rejection of an unsupported format, a too-large file and too many files;
- a resized and a JPEG-compressed copy is found as a duplicate of its original;
- no false duplicate for two different images;
- `?threshold=` overriding the default;
- 404 for an unknown `request_id` and an unknown image;
- a pair inside one request reported once; a copy uploaded in a later request is found too;
- the queue: concurrent workers never take the same image, and an image held by a crashed worker returns to the queue.

Test images are generated in the tests.

Frontend checks: `npm run build` (type check + build), `npm run lint`, `npm run format:check`.

## Configuration

All settings are environment variables with defaults in `backend/app/core/settings.py`. The full list is in `backend/.env.sample`. The main ones:

| Variable | Default | Meaning |
|---|---|---|
| `DUPLICATE_THRESHOLD` | `0.80` | Default similarity threshold (0–1). Can be overridden per call with `?threshold=`. |
| `MONGO_URL`, `MONGO_DB` | `mongodb://localhost:27017`, `dedup` | MongoDB address and database. |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant address. |
| `STORAGE_DIR` | `data/images` | Where originals and thumbnails are stored. |
| `MODEL_PATH` | `dedup_model/sscd_disc_mixup.torchscript.pt` | Path to the SSCD weights. Downloaded there if missing. |
| `MAX_FILE_BYTES`, `MAX_FILES_PER_REQUEST` | 10 MB, `50` | Upload limits. |
| `WORKERS` | `1` (`2` in compose) | Uvicorn processes for the API. |
| `TORCH_THREADS`, `WORKER_BATCH_SIZE` | `0` (all cores), `64` | Per-worker CPU threads and batch size. |

## API

Full interactive docs are at http://localhost:8000/docs.

### `POST /images`

`multipart/form-data` with one or more `files` (JPEG or PNG, at most 10 MB each, at most 50 per request). Invalid files do not fail the request; they are skipped and listed with a reason (`unsupported_format`, `file_too_large`, `invalid_image`, `empty_file`). More than 50 files, or a body over the total limit, returns `413`.

```json
{
  "request_id": "b3f1c2e4-...",
  "accepted": 8,
  "rejected": [
    {"filename": "big.png", "reason": "file_too_large"},
    {"filename": "doc.pdf", "reason": "unsupported_format"}
  ]
}
```

The response comes back right away. Embedding happens in the background.

### `GET /duplicates/{request_id}?threshold=0.9`

Returns duplicate groups for the request's images. While images are still being embedded, `status` is `"processing"` and `groups` is empty; the client polls until `status` is `"done"`. An unknown `request_id` returns `404`.

```json
{
  "request_id": "b3f1c2e4-...",
  "status": "done",
  "accepted": 8,
  "rejected": [],
  "groups": [
    {
      "image_id": "img_1f0c...",
      "filename": "coin_front.jpg",
      "duplicates": [
        {"image_id": "img_7a2b...", "filename": "coin_front_small.jpg", "score": 0.983, "source_request_id": "a91d..."}
      ]
    }
  ],
  "failed": [],
  "message": null
}
```

- Duplicates are searched among the images of this request and all other images in the store at the time of the call, including ones uploaded after this request. So the result of an older request can grow when new copies arrive.
- If two images of the same request match each other, the pair is shown once, under the first of them.
- `score` is the cosine similarity of the two embeddings (1.0 means identical).
- `failed` lists accepted files that the worker could not decode.
- If nothing is found, `groups` is empty and `message` is `"No duplicates found"`.

### `GET /images/{image_id}?thumb=true`

Returns the original image, or with `thumb=true` a 256 px WebP thumbnail. Files never change once written, so they are served with a long-lived cache header.

## Architecture

```
                 ┌──────────────┐
  Browser ──────▶│   frontend   │  React SPA served by nginx, /api/* proxied to the API
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐   originals   ┌─────────────────┐
                 │     api      │──────────────▶│  image storage  │
                 │  (FastAPI)   │               │ (shared volume) │
                 └──┬────────┬──┘               └────────▲────────┘
       requests,    │        │ vector search              │ originals,
       image queue  │        │                            │ thumbnails
                 ┌──▼──────┐ │  ┌──────────┐     ┌────────┴────────┐
                 │ MongoDB │◀┼──┤  Qdrant  │◀────┤  worker × N     │
                 └─────────┘ │  └────▲─────┘     │ (PyTorch, SSCD) │
                      ▲      └───────┘           └────────┬────────┘
                      └───────────────────────────────────┘
                              claim batch / write status
```

**Upload (`POST /images`).** The API validates each file, saves the bytes under their sha256 (identical files are stored once), and writes one MongoDB document per image with status `pending`. It never runs the model, so the response does not wait for embedding.

**Embedding (workers).** Each worker takes a batch of pending images from MongoDB, decodes them, saves a thumbnail, computes SSCD embeddings in one batch and writes the vectors to Qdrant. The image is then marked `done`, or `failed` if it could not be decoded. Byte-identical files that were already embedded reuse the stored vector instead of running the model.

The queue is the `images` collection itself:
- a worker claims a batch with a conditional update and a claim token, so even when several workers race for the same images, each image ends up with exactly one of them;
- a claim has a lease (5 minutes by default). If a worker crashes, its images return to the queue when the lease expires, and the token stops the late worker from overwriting the new owner's result.

**Search (`GET /duplicates`).** Search runs at read time, not at upload time:
1. The API loads the request's vectors from Qdrant.
2. It sends one batched query with the threshold.
3. It groups the hits.

Because of this, changing `?threshold=` needs no reprocessing, and the UI slider updates the results instantly. Qdrant keeps `filename` and `request_id` in each point's payload, so building the response needs no extra MongoDB lookups.

**Storage roles:**

| Store | Holds |
|---|---|
| MongoDB | requests, image metadata, processing status (also the work queue) |
| Qdrant | one 512-d vector per image, plus filename and request ID |
| Disk volume | original files and thumbnails, addressed by sha256 |

**Code layout.**
- `backend/app` is layered:
  - `routers` → `services` → `db/repositories`;
  - `schemas` (API models), `models` (MongoDB documents);
  - `ml/embedder.py` (model), `utils` (image decoding, file storage);
  - `core` (settings, constants, exceptions).
- `frontend/src` has `pages`, `components` (`components/ui` are the shadcn primitives), `hooks`, and `lib` (API hooks on TanStack Query, error messages, constants).

**Frontend.** Vite, React, TypeScript, Tailwind, shadcn/ui, TanStack Query, React Router. It covers everything the task requires:
- multi-file selection and drag & drop with previews;
- client-side format and size checks;
- upload and processing indicators;
- results grouped with thumbnails and scores;
- opening a request by ID;
- error messages for an unreachable server, 404, 413 and 5xx.

It also covers all the optional items: the threshold slider, full-size view on click, recent request history (in `localStorage`) and a responsive layout.

**Scaling.** The layout is designed so each part scales on its own:
- **Workers** are stateless. Run more of them (`--scale worker=N`), or on other machines once storage is moved to S3 (see below).
- **API processes** are set by `WORKERS`.
- **Qdrant** keeps an int8-quantized copy of the vectors in RAM for search, with full-precision vectors on disk used only to re-score the top candidates. This takes about 4× less memory: roughly 5 GB instead of 20 GB for 10 million images. It was not load-tested at that size.

## Why this model, store and threshold

### Model: SSCD

[SSCD](https://github.com/facebookresearch/sscd-copy-detection) (Meta, ResNet50, 512-d) is a model trained specifically for **image copy detection**. It learns to match edited copies of a picture (crops, flips, compression, overlays) while keeping different photos of similar things apart. The checkpoint is `sscd_disc_mixup`, the one the authors recommend.

It was compared on real photos (the UKBench dataset) with the models the task suggests: DINOv2, EfficientNet, ResNet50, ViT and CLIP. The hard case is two different shots of the same object, exactly the task's "similar in content, but not a duplicate".

| Model | AUC | Duplicates found | False matches, same object | Images/s (CPU) |
|---|---|---|---|---|
| **SSCD** | **0.960** | **89.0%** | **9.6%** | 13 |
| DINOv2 ViT-S/14 | 0.866 | 76.4% | 17.3% | 50 |
| EfficientNet-B0 | 0.849 | 71.8% | 16.0% | 13 |
| ViT-B/16 | 0.832 | 71.2% | 17.1% | 21 |
| ResNet50 | 0.795 | 59.5% | 12.9% | 11 |
| CLIP ViT-B/32 | 0.524 | 23.5% | 17.8% | 77 |

Each row is at that model's best threshold. General-purpose models are trained to recognize *what* is in a photo, so different shots of the same object look almost identical to them. CLIP is close to guessing.

SSCD is the most accurate by a wide margin. DINOv2 is about 4× faster, but a missed or false duplicate is an error the user sees, while throughput can be bought with more workers.

Data, methodology and full results are in [CALIBRATION.md](CALIBRATION.md).

### Vector store: Qdrant

- **Search with a score threshold** in one query: "all neighbours above 0.80" is a single request, not search-then-filter in Python.
- **Batched queries**: all images of a request are searched in one round-trip.
- **Runs as its own service** with persistence, so the API and any number of workers share it. Faiss and Annoy are libraries inside one process: every process would need its own copy of the index, and Annoy cannot add items to a built index.
- **Scalar quantization and on-disk vectors** keep memory low as the collection grows.
- **An in-memory mode** (`QDRANT_URL=":memory:"`) lets the tests run without a server.

MongoDB holds everything that is not a vector: requests, image metadata, statuses and the work queue. This avoids adding a separate message broker to the stack.

### Threshold: 0.80

The SSCD scores were measured on 2400 duplicate pairs (16 kinds of edits that cover the task's definition), 450 "same object, other photo" pairs and 150 "different object" pairs:

| Threshold | Duplicates found | False: same object | False: other object |
|---|---|---|---|
| 0.75 | 90.2% | 12.2% | 0.0% |
| **0.80** | **79.8%** | **6.0%** | **0.0%** |
| 0.85 | 65.1% | 1.1% | 0.0% |

The best balance of "found minus false" was at 0.76. The task, however, stresses that images similar in content are **not** duplicates, so a false match is treated as the worse error. At 0.80, false matches on different shots of the same object drop by half (12% → 6%) at the cost of about 10 points of recall.

Resize, moderate compression, brightness, contrast, flip, watermark and 10% crops are found almost always. 20% crops, 5° rotation and combined edits sit just above the threshold. Different objects are never confused: the highest score between them is 0.37.

Use 0.75 to catch more heavily edited copies, or 0.85 for a strict mode. The threshold can be changed with `DUPLICATE_THRESHOLD`, per call with `?threshold=`, or with the slider in the UI.

## Deviations from the task

- **Only `multipart/form-data` uploads.** Base64 and URL input (optional in the task) are not implemented.
- **The duplicates response has extra fields** beyond the example: `accepted`, `rejected` and `failed`, so the UI can show the request summary from one call.

## Known limitations and possible improvements

**Detection quality**

- **10° rotation and very heavy JPEG compression (quality 10) are mostly missed.** Their typical score is below 0.80. Larger rotations (90°) and vertical flips are not covered at all. Fix: lower the threshold, or also index rotated/flipped variants of each image at the cost of more vectors.
- **The threshold was calibrated on a small, single-domain sample**: 150 objects from UKBench, objects on a table, synthetic edits. For a specific real-world domain it should be re-checked on that data.

**Infrastructure**

- **Store images in S3 instead of on the server's disk.** Originals and thumbnails currently live on a Docker volume shared by `api` and `worker`. This works while all services run on one host. Moving files to object storage (S3 or S3-compatible):
  - lets the `api` and workers run on different machines;
  - takes disk space and backups off the server;
  - lets the browser load images straight from S3/CDN via presigned URLs instead of through the API.

  In code, `LocalStorage` (`backend/app/utils/storage.py`) would be replaced with an S3 implementation of the same methods, and `GET /images/{id}` would redirect to a presigned URL instead of serving a local file. The sha256-based addressing stays the same.
- **The queue polls MongoDB.** Idle workers check for new images every 0.5 s. This is simple and needs no extra service. At high volume, a real broker (RabbitMQ, Redis Streams, SQS) or MongoDB change streams (which need a replica set) would remove the polling and the per-batch claim queries.
- **Partial failures can leave orphan files.** If the MongoDB write fails after files were saved, those files stay on disk with no record pointing at them. They are harmless (content-addressed, reused by a later upload of the same bytes), but a periodic cleanup job would reclaim the space.
- **No deletion, authentication or rate limiting.** Every uploaded image stays in the index forever, and the API is open. A real deployment would need users/tenants, per-tenant search filters and limits.
- **Search runs on every `GET /duplicates`.** This keeps `?threshold=` free, but a busy client polling a large request repeats the same vector queries. Caching results per `(request_id, threshold)` would help.
- **No frontend tests** (optional in the task). The frontend is checked by the type checker, linter and manual testing.
