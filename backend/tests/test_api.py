import io
from PIL import Image


def test_upload_image(client):
    """Test uploading an image"""
    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    response = client.post(
        "/api/upload/image",
        files={"file": ("test.png", img_bytes, "image/png")},
        data={"image_type": "original"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "image_id" in data
    assert "type" in data
    assert "filename" in data
    assert data["type"] == "original"
    assert data["filename"] == "test.png"


def test_run_with_points(client):
    """Test mask generation with points"""
    # First, upload an image
    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    upload_response = client.post(
        "/api/upload/image",
        files={"file": ("test.png", img_bytes, "image/png")},
        data={"image_type": "original"},
    )
    image_id = upload_response.json()["image_id"]

    # Generate masks with points
    response = client.post(
        "/api/run",
        data={
            "original_image_id": image_id,
            "points": '[{"x": 50, "y": 50}]',
            "labels": '[1]',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 3  # Should return 3 candidate masks


def test_run_with_multiple_points(client):
    """Test mask generation with multiple points"""
    # Upload image
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    upload_response = client.post(
        "/api/upload/image",
        files={"file": ("test.png", img_bytes, "image/png")},
        data={"image_type": "original"},
    )
    image_id = upload_response.json()["image_id"]

    # Generate masks with multiple points
    response = client.post(
        "/api/run",
        data={
            "original_image_id": image_id,
            "points": '[{"x": 10, "y": 20}, {"x": 30, "y": 40}]',
            "labels": '[1, 1]',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 3  # Should return 3 candidate masks

    # Verify structure of each result
    for result in data["results"]:
        assert "masked_image" in result
        assert "mask" in result
        assert "score" in result
        assert result["masked_image"].startswith("data:image/png;base64,")
        assert result["mask"].startswith("data:image/png;base64,")


def test_sam_mask_generation(client):
    """Test SAM mask generation with a single point"""
    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Upload the image
    upload_response = client.post(
        "/api/upload/image",
        files={"file": ("test.png", img_bytes, "image/png")},
        data={"image_type": "original"},
    )
    image_id = upload_response.json()["image_id"]

    # Call the run endpoint with a single point - should return results synchronously
    response = client.post(
        "/api/run",
        data={
            "original_image_id": image_id,
            "points": '[{"x": 50, "y": 50}]',
            "labels": '[1]',
        },
    )

    # Check for 200 status
    assert response.status_code == 200

    # Verify results structure
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 3  # Should return 3 candidate masks
