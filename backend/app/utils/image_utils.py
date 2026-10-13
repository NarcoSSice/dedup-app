import io
import uuid

from PIL import Image, ImageOps, UnidentifiedImageError

from core.constants import IMAGE_ID_PREFIX, SUPPORTED_FORMATS
from core.enums.image import RejectReason
from core.exceptions.image import InvalidImageError


def to_public_id(image_id: str) -> str:
    """UUID -> img_<32 hex chars>"""
    return f"{IMAGE_ID_PREFIX}{uuid.UUID(image_id).hex}"


def parse_public_id(public_id: str) -> str | None:
    try:
        return str(uuid.UUID(public_id.removeprefix(IMAGE_ID_PREFIX)))
    except ValueError:
        return None


def validate_image(data: bytes, max_bytes: int) -> str:
    """Return content type or raise InvalidImageError. The format is sniffed
    from the bytes: filename and Content-Type are client-controlled."""
    if len(data) > max_bytes:
        raise InvalidImageError(RejectReason.file_too_large)
    if not data:
        raise InvalidImageError(RejectReason.empty_file)
    try:
        img = Image.open(io.BytesIO(data))
        image_format = img.format
        if image_format not in SUPPORTED_FORMATS:
            raise InvalidImageError(RejectReason.unsupported_format)
        img.verify()
    except UnidentifiedImageError:
        raise InvalidImageError(RejectReason.unsupported_format) from None
    except InvalidImageError:
        raise
    except Exception:
        raise InvalidImageError(RejectReason.invalid_image) from None
    return SUPPORTED_FORMATS[image_format]


def decode_image(data: bytes, min_side: int) -> Image.Image:
    """Decode to RGB. JPEG is decoded straight at reduced scale (DCT draft mode),
    several times faster for large photos than full decode + resize."""
    img = Image.open(io.BytesIO(data))
    img.draft("RGB", (min_side, min_side))  # no-op for PNG
    img = ImageOps.exif_transpose(img)  # phone photos store rotation in EXIF
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.getchannel("A"))
        return background
    return img.convert("RGB")


def make_thumbnail(img: Image.Image, size: int) -> bytes:
    img = img.copy()
    img.thumbnail((size, size))
    buffer = io.BytesIO()
    img.save(buffer, "WEBP", quality=80)
    return buffer.getvalue()
