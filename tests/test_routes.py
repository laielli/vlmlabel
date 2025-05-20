import os
import io
import pytest

from app import app


def test_root_returns_200_when_frames_present(tmp_path):
    # Create a temporary frames directory with one dummy image
    frames_dir = tmp_path / 'frames'
    frames_dir.mkdir()
    (frames_dir / 'frame_0001.jpg').write_bytes(b'fake')

    original_static_folder = app.static_folder
    app.static_folder = str(tmp_path)
    try:
        client = app.test_client()
        response = client.get('/')
        assert response.status_code == 200
    finally:
        app.static_folder = original_static_folder


def test_load_annotations_empty_csv():
    client = app.test_client()
    data = {
        'file': (io.BytesIO(b''), 'test.csv')
    }
    response = client.post('/load_annotations', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['message'] == 'Empty CSV file'
