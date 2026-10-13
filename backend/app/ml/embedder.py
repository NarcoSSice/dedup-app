import os
from functools import cached_property

import numpy as np
import torch
from PIL import Image

from core.constants import MODEL_INPUT_SIZE, MODEL_URL
from core.settings import settings

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class Embedder:
    """SSCD copy-detection descriptors (Meta, ResNet50 -> 512-d, L2-normalized).
    Trained specifically to match edited copies (crops, flips, compression,
    overlays) while keeping different photos of similar things apart."""

    @cached_property
    def model(self) -> torch.jit.ScriptModule:
        path = settings.worker.MODEL_PATH
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            torch.hub.download_url_to_file(MODEL_URL, path)
        if settings.worker.TORCH_THREADS:
            torch.set_num_threads(settings.worker.TORCH_THREADS)
        return torch.jit.load(path, map_location="cpu").eval()

    @cached_property
    def dim(self) -> int:
        return self.embed([Image.new("RGB", (8, 8))]).shape[1]

    def embed(self, images: list[Image.Image]) -> np.ndarray:
        """Batch of RGB images -> (N, D) float32 unit vectors."""
        size = (MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)
        # squash to a square instead of center-crop, so crops/borders stay in view
        batch = np.stack(
            [
                np.asarray(img.resize(size, Image.BILINEAR), dtype=np.float32)
                for img in images
            ]
        )
        batch = (batch / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
        tensor = torch.from_numpy(batch).permute(0, 3, 1, 2).contiguous()
        with torch.inference_mode():
            vectors = self.model(tensor)
        return torch.nn.functional.normalize(vectors, dim=1).numpy()


embedder = Embedder()
