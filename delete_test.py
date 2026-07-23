import time

import pytest

from conftest import md5_of, wait_until_status


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


class TestDeleteResource:
    def test_file_permanently(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        response = disk_client.delete(path, permanently=True)
        assert response.status_code == 204, response.text

        disk_check = disk_client.get_resource(path)
        assert disk_check.status_code == 404

        trash_check = disk_client.get_trash_resource(path)
        assert trash_check.status_code == 404

    def test_folder_permanently(self, disk_client, uploaded_folder):
        path = uploaded_folder

        response = disk_client.delete(path, permanently=True)
        assert response.status_code == 204, response.text

        disk_check = disk_client.get_resource(path)
        assert disk_check.status_code == 404

        trash_check = disk_client.get_trash_resource(path)
        assert trash_check.status_code == 404

    def test_file_to_trash(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        response = disk_client.delete(path)
        assert response.status_code in (202, 204), response.text

        if response.status_code == 202:
            operation_href = response.json()["href"]
            status = _wait_operation_finished(disk_client, operation_href)
            assert status == "success"

        disk_check = wait_until_status(lambda: disk_client.get_resource(path), 404)
        assert disk_check.status_code == 404

        trash_check = disk_client.get_trash_resource(path)
        assert trash_check.status_code == 200
        assert trash_check.json()["type"] == "file"

        disk_client.delete(path, permanently=True)

    def test_folder_to_trash(self, disk_client, uploaded_folder):
        path = uploaded_folder

        response = disk_client.delete(path)
        assert response.status_code in (202, 204), response.text

        if response.status_code == 202:
            operation_href = response.json()["href"]
            status = _wait_operation_finished(disk_client, operation_href)
            assert status == "success"

        disk_check = disk_client.get_resource(path)
        assert disk_check.status_code == 404

        trash_check = wait_until_status(lambda: disk_client.get_trash_resource(path), 200)
        assert trash_check.status_code == 200
        assert trash_check.json()["type"] == "dir"

        disk_client.delete(path, permanently=True)

    def test_with_invalid_md5(self, disk_client, uploaded_file):
        path, content = uploaded_file
        wrong_md5 = md5_of(b"not the real content")

        response = disk_client.delete(path, permanently=True, md5=wrong_md5)
        assert response.status_code == 409, response.text

        disk_check = disk_client.get_resource(path)
        assert disk_check.status_code == 200
        assert disk_check.json()["md5"] == md5_of(content)

        trash_check = disk_client.get_trash_resource(path)
        assert trash_check.status_code == 404

    def test_with_correct_md5(self, disk_client, uploaded_file):
        path, content = uploaded_file
        correct_md5 = md5_of(content)

        response = disk_client.delete(path, permanently=True, md5=correct_md5)
        assert response.status_code == 204, response.text

        disk_check = disk_client.get_resource(path)
        assert disk_check.status_code == 404

    def test_nonexistent_file_returns_404(self, disk_client):
        fake_path = "/no_such_file_delete_test.txt"

        response = disk_client.delete(fake_path, permanently=True)

        assert response.status_code == 404, response.text
        assert response.json()["error"] == "DiskNotFoundError"

    def test_without_path_returns_400(self, disk_client):
        response = disk_client.delete("")

        assert response.status_code == 400, response.text

    def test_permission_not_readonly(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        response = disk_client.delete(path, permanently=True)

        assert response.status_code != 403, (
            "Токен не имеет прав на удаление (403 Forbidden). "
            "Проверьте права выданного OAuth-токена."
        )
        assert response.status_code == 204, response.text

        disk_check = wait_until_status(lambda: disk_client.get_resource(path), 404)
        assert disk_check.status_code == 404

    def test_with_force_async_true(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        response = disk_client.delete(path, permanently=True, force_async=True)

        assert response.status_code == 202, response.text
        operation_href = response.json()["href"]

        status = _wait_operation_finished(disk_client, operation_href)
        assert status == "success"

        disk_check = disk_client.get_resource(path)
        assert disk_check.status_code == 404