IMAGE_ID_PREFIX = "img_"
NO_DUPLICATES_MESSAGE = "No duplicates found"

# PIL format name -> content type
SUPPORTED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png"}
THUMBNAIL_CONTENT_TYPE = "image/webp"
IMMUTABLE_CACHE_HEADER = "public, max-age=31536000, immutable"

QDRANT_COLLECTION = "images"
MODEL_URL = (
    "https://dl.fbaipublicfiles.com/sscd-copy-detection/sscd_disc_mixup.torchscript.pt"
)
# SSCD input resolution; the threshold in CALIBRATION.md is valid only for it
MODEL_INPUT_SIZE = 224
THUMB_SIZE = 256
