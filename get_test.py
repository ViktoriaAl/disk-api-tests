from conftest import md5_of


class TestGetResource:

    def test_file_success(self, disk_client, uploaded_file):
        path, content = uploaded_file

        response = disk_client.get_resource(path)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == path.lstrip("/")
        assert data["type"] == "file"
        assert data["size"] == len(content)

    def test_folder_success(self, disk_client, uploaded_folder):
        path = uploaded_folder

        response = disk_client.get_resource(path)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == path.lstrip("/")
        assert data["type"] == "dir"

    def test_nonexistent_returns_404(self, disk_client):
        response = disk_client.get_resource("/no_such_resource_get_test.txt")

        assert response.status_code == 404, response.text
        assert response.json()["error"] == "DiskNotFoundError"

    def test_without_path_returns_400(self, disk_client):
        response = disk_client.get_resource("")

        assert response.status_code == 400, response.text

    def test_with_fields_param(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        response = disk_client.get_resource(path, fields="name,type")

        assert response.status_code == 200, response.text
        assert set(response.json().keys()) == {"name", "type"}

    def test_folder_with_limit(self, disk_client, uploaded_folder):
        folder_path = uploaded_folder
        for i in range(3):
            disk_client.upload_file(f"{folder_path}/file_{i}.txt", b"data", overwrite=True)

        response = disk_client.get_resource(folder_path, limit=2)

        assert response.status_code == 200, response.text
        items = response.json()["_embedded"]["items"]
        assert len(items) <= 2

    def test_md5_matches_content(self, disk_client, uploaded_file):
        path, content = uploaded_file

        response = disk_client.get_resource(path, fields="md5")

        assert response.status_code == 200, response.text
        assert response.json()["md5"] == md5_of(content)

    def test_size_matches_content(self, disk_client, uploaded_file):
        path, content = uploaded_file

        response = disk_client.get_resource(path)

        assert response.status_code == 200, response.text
        assert response.json()["size"] == len(content)

    def test_depth_folder_structure(self, disk_client, uploaded_folder):
        parent = uploaded_folder
        child_folder = f"{parent}/child_dir"
        disk_client.create_folder(child_folder)
        disk_client.upload_file(f"{child_folder}/nested_file.txt", b"nested", overwrite=True)

        response = disk_client.get_resource(parent)

        assert response.status_code == 200, response.text
        items = response.json()["_embedded"]["items"]
        names = [item["name"] for item in items]
        assert "child_dir" in names

        child_response = disk_client.get_resource(child_folder)
        assert child_response.status_code == 200
        child_items = child_response.json()["_embedded"]["items"]
        child_names = [item["name"] for item in child_items]
        assert "nested_file.txt" in child_names

        disk_client.delete(child_folder, permanently=True)

    def test_after_delete_returns_404(self, disk_client, uploaded_file):
        path, _ = uploaded_file

        delete_response = disk_client.delete(path, permanently=True)
        assert delete_response.status_code == 204

        response = disk_client.get_resource(path)

        assert response.status_code == 404, response.text
        assert response.json()["error"] == "DiskNotFoundError"