import time
import uuid

import pytest

from conftest import md5_of


def _wait_operation_finished(disk_client, operation_href, timeout=40, interval=2):
    deadline = time.time() + timeout
    status = None

    while time.time() < deadline:
        resp = disk_client.get_operation_status(operation_href)
        assert resp.status_code == 200
        status = resp.json()["status"]
        if status in ("success", "failed"):
            return status
        time.sleep(interval)

    pytest.fail(f"Операция не завершилась за {timeout} секунд, статус: {status}")


class TestPostCopyResource:
    def test_success(self, disk_client, uploaded_file):
        from_path, content = uploaded_file
        to_path = f"/test_copy_{uuid.uuid4().hex[:8]}.txt"

        response = disk_client.copy(from_path, to_path)
        assert response.status_code in (201, 202), response.text

        if response.status_code == 202:
            status = _wait_operation_finished(disk_client, response.json()["href"])
            assert status == "success"

        source_check = disk_client.get_resource(from_path)
        assert source_check.status_code == 200

        dest_check = disk_client.get_resource(to_path)
        assert dest_check.status_code == 200
        assert dest_check.json()["size"] == len(content)

        disk_client.delete(to_path, permanently=True)

    def test_conflict_without_overwrite(self, disk_client, uploaded_file):
        from_path, content = uploaded_file
        to_path = f"/test_copy_target_{uuid.uuid4().hex[:8]}.txt"
        occupy_resp = disk_client.upload_file(to_path, b"already here", overwrite=True)
        assert occupy_resp.status_code == 201

        response = disk_client.copy(from_path, to_path)
        assert response.status_code == 409, response.text

        disk_client.delete(to_path, permanently=True)

    def test_overwrite_success(self, disk_client, uploaded_file):
        from_path, content = uploaded_file
        to_path = f"/test_copy_overwrite_{uuid.uuid4().hex[:8]}.txt"

        occupy_resp = disk_client.upload_file(to_path, b"old content", overwrite=True)
        assert occupy_resp.status_code == 201

        response = disk_client.copy(from_path, to_path, overwrite=True)
        assert response.status_code in (201, 202), response.text

        if response.status_code == 202:
            status = _wait_operation_finished(disk_client, response.json()["href"])
            assert status == "success"

        dest_check = disk_client.get_resource(to_path)
        assert dest_check.status_code == 200
        assert dest_check.json()["size"] == len(content)
        assert dest_check.json()["md5"] == md5_of(content)

        disk_client.delete(to_path, permanently=True)

    def test_nonexistent_source_returns_404(self, disk_client):
        from_path = f"/no_such_source_{uuid.uuid4().hex[:8]}.txt"
        to_path = f"/test_copy_dest_{uuid.uuid4().hex[:8]}.txt"

        response = disk_client.copy(from_path, to_path)

        assert response.status_code == 404, response.text

    def test_without_required_params_400(self, disk_client, uploaded_file):
        from_path, _ = uploaded_file

        response_no_to = disk_client.copy(from_path, "")
        assert response_no_to.status_code == 400, response_no_to.text

        response_no_from = disk_client.copy("", "/test_target.txt")
        assert response_no_from.status_code == 400, response_no_from.text

    def test_force_async(self, disk_client, uploaded_file):
        from_path, _ = uploaded_file
        to_path = f"/test_copy_async_{uuid.uuid4().hex[:8]}.txt"

        response = disk_client.copy(from_path, to_path, force_async=True)

        assert response.status_code == 202, response.text
        status = _wait_operation_finished(disk_client, response.json()["href"])
        assert status == "success"

        dest_check = disk_client.get_resource(to_path)
        assert dest_check.status_code == 200

        disk_client.delete(to_path, permanently=True)

    def test_size_matches_source(self, disk_client, uploaded_file):
        from_path, content = uploaded_file
        to_path = f"/test_copy_size_{uuid.uuid4().hex[:8]}.txt"

        response = disk_client.copy(from_path, to_path)
        assert response.status_code in (201, 202), response.text

        if response.status_code == 202:
            status = _wait_operation_finished(disk_client, response.json()["href"])
            assert status == "success"

        source_size = disk_client.get_resource(from_path).json()["size"]
        dest_size = disk_client.get_resource(to_path).json()["size"]

        assert dest_size == source_size == len(content)

        disk_client.delete(to_path, permanently=True)