import os
from functools import cached_property

import numpy as np
import torch
from PIL import Image

from core.settings import settings

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class Embedder:
    """SSCD copy-detection descriptors (Meta, ResNet50 -> 512-d, L2-normalized).
    Trained specifically to match edited copies (crops, flips, compression,
    overlays) while keeping different photos of similar things apart."""

    def __init__(self, model_path: str, model_url: str, input_size: int):
        self.model_path = model_path
        self.model_url = model_url
        self.input_size = input_size

    @cached_property
    def model(self) -> torch.jit.ScriptModule:
        if not os.path.exists(self.model_path):
            os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
            torch.hub.download_url_to_file(self.model_url, self.model_path)
        if settings.model.TORCH_THREADS:
            torch.set_num_threads(settings.model.TORCH_THREADS)
        return torch.jit.load(self.model_path, map_location="cpu").eval()

    @cached_property
    def dim(self) -> int:
        return self.embed([Image.new("RGB", (8, 8))]).shape[1]

    def embed(self, images: list[Image.Image]) -> np.ndarray:
        """Batch of RGB images -> (N, D) float32 unit vectors."""
        size = (self.input_size, self.input_size)
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


embedder = Embedder(settings.model.PATH, settings.model.URL, settings.model.INPUT_SIZE)
