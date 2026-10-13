import os
import uuid

from db.repositories.container import get_repositories
from tests.utils import make_image, png_file, to_bytes
from utils.image_utils import to_public_id


async def upload(client, *files):
    response = await client.post("/images", files=[("files", f) for f in files])
    assert response.status_code == 200, response.text
    return response.json()


async def test_upload_images(client):
    jpeg = ("b.jpg", to_bytes(make_image(2), "JPEG", quality=90), "image/jpeg")

    body = await upload(client, png_file("a.png", 1), jpeg)

    assert body["accepted"] == 2
    assert body["rejected"] == []
    uuid.UUID(body["request_id"])


async def test_rejects_bad_format_and_too_large(client):
    body = await upload(
        client,
        ("doc.pdf", b"%PDF-1.4\n%fake pdf", "application/pdf"),
        ("fake.png", b"not really a png", "image/png"),  # extension lies
        ("anim.gif", to_bytes(make_image(3), "GIF"), "image/gif"),
        ("big.png", b"\x89PNG\r\n\x1a\n" + os.urandom(10 * 1024 * 1024), "image/png"),
        png_file("ok.png", 4),  # a valid file in the same request still goes through
    )

    expected_rejected = [
        {"filename": "doc.pdf", "reason": "unsupported_format"},
        {"filename": "fake.png", "reason": "unsupported_format"},
        {"filename": "anim.gif", "reason": "unsupported_format"},
        {"filename": "big.png", "reason": "file_too_large"},
    ]
    assert body["accepted"] == 1
    assert body["rejected"] == expected_rejected

    # the same summary is available later by request id
    result = (await client.get(f"/duplicates/{body['request_id']}")).json()
    assert result["accepted"] == 1
    assert result["rejected"] == expected_rejected


async def test_too_many_files(client):
    files = [("files", (f"{i}.png", b"x", "image/png")) for i in range(51)]

    response = await client.post("/images", files=files)

    assert response.status_code == 413


async def test_get_image_and_thumbnail(client, process_queue):
    data = to_bytes(make_image(40))
    body = await upload(client, ("x.png", data, "image/png"))
    await process_queue()
    [image] = await get_repositories().images.get_request_images(body["request_id"])
    url = f"/images/{to_public_id(image.id)}"

    original = await client.get(url)
    assert original.status_code == 200
    assert original.content == data
    assert original.headers["content-type"] == "image/png"

    thumbnail = await client.get(url, params={"thumb": True})
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"] == "image/webp"


async def test_unknown_image_404(client):
    missing = to_public_id("00000000-0000-0000-0000-000000000000")
    assert (await client.get(f"/images/{missing}")).status_code == 404
    assert (await client.get("/images/garbage")).status_code == 404
