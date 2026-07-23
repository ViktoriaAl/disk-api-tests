import uuid

from conftest import md5_of


class TestPutResource:
    def test_folder_success(self, disk_client, uploaded_folder):
        path = uploaded_folder

        check = disk_client.get_resource(path)
        assert check.status_code == 200
        assert check.json()["type"] == "dir"

    def test_folder_conflict(self, disk_client, uploaded_folder):
        path = uploaded_folder

        response = disk_client.create_folder(path)

        assert response.status_code == 409, response.text

    def test_folder_without_path_returns_400(self, disk_client):
        response = disk_client.create_folder("")

        assert response.status_code == 400, response.text

    def test_folder_missing_parent(self, disk_client):
        missing_parent = f"/no_such_parent_{uuid.uuid4().hex[:8]}"
        child_path = f"{missing_parent}/child"

        response = disk_client.create_folder(child_path)

        assert response.status_code == 409, response.text

        check = disk_client.get_resource(child_path)
        assert check.status_code == 404

    def test_folder_with_existing_parent(self, disk_client, uploaded_folder):
        parent = uploaded_folder
        child_path = f"{parent}/child_ok"

        response = disk_client.create_folder(child_path)
        assert response.status_code == 201, response.text

        check = disk_client.get_resource(child_path)
        assert check.status_code == 200
        assert check.json()["type"] == "dir"

        disk_client.delete(child_path, permanently=True)

    def test_folder_depth_limit(self, disk_client, uploaded_folder):
        current_path = uploaded_folder
        max_depth_to_try = 30
        created_paths = []
        rejected = False
        rejected_at_depth = None

        for depth in range(1, max_depth_to_try + 1):
            current_path = f"{current_path}/d"
            response = disk_client.create_folder(current_path)
            if response.status_code == 201:
                created_paths.append(current_path)
            else:
                rejected = True
                rejected_at_depth = depth
                break

        if rejected:
            print(f"Сервер отклонил создание папки на глубине {rejected_at_depth}")
        else:
            print(
                f"Лимит вложенности не обнаружен в пределах {max_depth_to_try} "
                f"сервер успешно создал все папки"
            )

        for path in reversed(created_paths):
            disk_client.delete(path, permanently=True)

    def test_upload_file_success(self, disk_client, uploaded_file):
        path, content = uploaded_file

        check = disk_client.get_resource(path)
        assert check.status_code == 200
        assert check.json()["size"] == len(content)
        assert check.json()["md5"] == md5_of(content)

    def test_upload_file_conflict_without_overwrite(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        response = disk_client.upload_file(path, b"other content", overwrite=False)

        assert response.status_code == 409, response.text

    def test_upload_file_overwrite_success(self, disk_client, uploaded_file):
        path, _ = uploaded_file
        new_content = b"overwritten content"

        response = disk_client.upload_file(path, new_content, overwrite=True)
        assert response.status_code == 201, response.text

        check = disk_client.get_resource(path)
        assert check.status_code == 200
        assert check.json()["size"] == len(new_content)
        assert check.json()["md5"] == md5_of(new_content)

    def test_upload_empty_file(self, disk_client):
        path = f"/test_empty_{uuid.uuid4().hex[:8]}.txt"

        response = disk_client.upload_file(path, b"", overwrite=True)
        assert response.status_code == 201, response.text

        check = disk_client.get_resource(path)
        assert check.status_code == 200
        assert check.json()["size"] == 0

        disk_client.delete(path, permanently=True)

    def test_upload_small_file(self, disk_client):
        path = f"/test_small_{uuid.uuid4().hex[:8]}.txt"
        content = b"abc"

        response = disk_client.upload_file(path, content, overwrite=True)
        assert response.status_code == 201, response.text

        check = disk_client.get_resource(path)
        assert check.status_code == 200
        assert check.json()["size"] == len(content)

        disk_client.delete(path, permanently=True)

    def test_upload_large_file(self, disk_client):
        path = f"/test_large_{uuid.uuid4().hex[:8]}.bin"
        content = b"x" * (10 * 1024 * 1024) 

        response = disk_client.upload_file(path, content, overwrite=True)
        assert response.status_code == 201, response.text

        check = disk_client.get_resource(path)
        assert check.status_code == 200
        assert check.json()["size"] == len(content)

        disk_client.delete(path, permanently=True)
