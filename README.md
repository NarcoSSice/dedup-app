# Image Duplicate Finder

<!-- Draft: setup instructions and architecture overview will be added. -->

## Model and threshold choice

The **SSCD** model and the **0.75** threshold were chosen by testing on real photos (the UKBench dataset) against the models suggested in the task: DINOv2, EfficientNet, ResNet, ViT and CLIP. SSCD separates real copies from different photos of the same object better than any of them. Data, methodology and full results are in [CALIBRATION.md](CALIBRATION.md).

## Deviations from the task

- **The "no duplicates" message is in English** (`"No duplicates found"`) instead of the Ukrainian message given in the task, to keep the API in one language.

## Known limitations and possible improvements

- **Store images in S3 instead of on the server's disk.** Originals and thumbnails currently live on a Docker volume shared by `api` and `worker`. This works while all services run on one host. To spread `api` and workers across machines, files need to go to object storage (S3 or S3-compatible). It also takes disk space and backups off the server, and lets the browser load images straight from S3/CDN via presigned URLs instead of going through the API. In code, only `LocalStorage` (`backend/app/utils/storage.py`) needs to be replaced with an S3 implementation exposing the same `put`/`get` methods; the sha256-based file addressing stays the same.
