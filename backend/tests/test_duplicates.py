import uuid

from core.constants import NO_DUPLICATES_MESSAGE
from tests.utils import make_image, png_file, to_bytes, upload


async def test_finds_resized_and_compressed_duplicate(client, process_queue):
    original = make_image(10, (800, 600))
    first = await upload(client, ("coin.png", to_bytes(original), "image/png"))
    small_copy = to_bytes(original.resize((400, 300)), "JPEG", quality=60)
    second = await upload(
        client,
        ("coin_small.jpg", small_copy, "image/jpeg"),
        png_file("other.png", 11),
    )
    request_id = second["request_id"]

    pending = (await client.get(f"/duplicates/{request_id}")).json()
    assert pending["status"] == "processing"

    await process_queue()
    body = (await client.get(f"/duplicates/{request_id}")).json()

    assert body["status"] == "done"
    assert body["message"] is None
    assert len(body["groups"]) == 1
    group = body["groups"][0]
    assert group["filename"] == "coin_small.jpg"
    [duplicate] = group["duplicates"]
    assert duplicate["filename"] == "coin.png"
    assert duplicate["source_request_id"] == first["request_id"]
    assert 0.8 < duplicate["score"] <= 1.0


async def test_threshold_override(client, process_queue):
    original = make_image(12)
    body = await upload(
        client,
        ("a.png", to_bytes(original), "image/png"),
        ("a_small.jpg", to_bytes(original.resize((256, 256)), "JPEG"), "image/jpeg"),
    )
    await process_queue()
    url = f"/duplicates/{body['request_id']}"

    assert len((await client.get(url)).json()["groups"]) == 1
    # only byte-identical copies reach 1.0
    strict = (await client.get(url, params={"threshold": 1.0})).json()
    assert strict["groups"] == []
    assert (await client.get(url, params={"threshold": 1.5})).status_code == 422


async def test_pair_within_one_request_reported_once(client, process_queue):
    original = make_image(20)
    body = await upload(
        client,
        ("a.png", to_bytes(original), "image/png"),
        ("a.jpg", to_bytes(original, "JPEG", quality=70), "image/jpeg"),
    )
    await process_queue()

    groups = (await client.get(f"/duplicates/{body['request_id']}")).json()["groups"]

    assert [
        (g["filename"], [d["filename"] for d in g["duplicates"]]) for g in groups
    ] == [("a.png", ["a.jpg"])]


async def test_finds_images_uploaded_later(client, process_queue):
    original = make_image(25)
    first = await upload(client, ("a.png", to_bytes(original), "image/png"))
    second = await upload(client, ("a.jpg", to_bytes(original, "JPEG"), "image/jpeg"))
    await process_queue()

    body = (await client.get(f"/duplicates/{first['request_id']}")).json()

    [group] = body["groups"]
    assert [(d["filename"], d["source_request_id"]) for d in group["duplicates"]] == [
        ("a.jpg", second["request_id"])
    ]


async def test_no_false_duplicate(client, process_queue):
    body = await upload(client, png_file("one.png", 30), png_file("two.png", 31))
    await process_queue()

    result = (await client.get(f"/duplicates/{body['request_id']}")).json()

    assert result["status"] == "done"
    assert result["groups"] == []
    assert result["message"] == NO_DUPLICATES_MESSAGE


async def test_unknown_request_404(client):
    response = await client.get(f"/duplicates/{uuid.uuid4()}")

    assert response.status_code == 404
