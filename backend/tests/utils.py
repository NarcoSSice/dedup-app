import io
import random

from PIL import Image, ImageDraw


def make_image(seed: int, size: tuple[int, int] = (512, 512)) -> Image.Image:
    """Synthetic 'photo': gradient background + random shapes.
    Different seed = visually different image."""
    rnd = random.Random(seed)
    width, height = size
    top, bottom = [tuple(rnd.randrange(256) for _ in range(3)) for _ in range(2)]

    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / height
        draw.line(
            [(0, y), (width, y)],
            fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bottom, strict=True)),
        )
    for _ in range(25):
        xs, ys = (
            sorted(rnd.sample(range(width), 2)),
            sorted(rnd.sample(range(height), 2)),
        )
        color = tuple(rnd.randrange(256) for _ in range(3))
        shape = rnd.choice([draw.ellipse, draw.rectangle])
        shape([xs[0], ys[0], xs[1], ys[1]], fill=color)
        draw.line(
            [
                rnd.randrange(width),
                rnd.randrange(height),
                rnd.randrange(width),
                rnd.randrange(height),
            ],
            fill=color,
            width=rnd.randrange(2, 12),
        )
    return img


def to_bytes(img: Image.Image, image_format: str = "PNG", **kwargs) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, image_format, **kwargs)
    return buffer.getvalue()


def png_file(filename: str, seed: int) -> tuple[str, bytes, str]:
    return filename, to_bytes(make_image(seed)), "image/png"
