import hashlib
import uuid
 
import pytest
import requests
import time
 
from config import BASE_URL, HEADERS
 
 
class DiskClient:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def get_resource(self, path, **params):
        params["path"] = path
        return requests.get(
            f"{self.base_url}/v1/disk/resources",
            headers=self.headers,
            params=params,
        )
 
    def get_trash_resource(self, path, **params):
        params["path"] = path
        return requests.get(
            f"{self.base_url}/v1/disk/trash/resources",
            headers=self.headers,
            params=params,
        )
 
    def get_disk_info(self):
        return requests.get(
            f"{self.base_url}/v1/disk",
            headers=self.headers,
        )
 
    def get_upload_link(self, path, **params):
        params["path"] = path
        return requests.get(
            f"{self.base_url}/v1/disk/resources/upload",
            headers=self.headers,
            params=params,
        )
 
    def get_operation_status(self, href):
        return requests.get(href, headers=self.headers)
 
    def create_folder(self, path, **params):
        params["path"] = path
        return requests.put(
            f"{self.base_url}/v1/disk/resources",
            headers=self.headers,
            params=params,
        )
 
    def upload_file(self, path, content: bytes, overwrite=False):
        link_resp = self.get_upload_link(path, overwrite=str(overwrite).lower())
        if link_resp.status_code != 200:
            return link_resp
        upload_url = link_resp.json()["href"]
        return requests.put(upload_url, data=content)
 
    def copy(self, from_path, to_path, **params):
        params["from"] = from_path
        params["path"] = to_path
        return requests.post(
            f"{self.base_url}/v1/disk/resources/copy",
            headers=self.headers,
            params=params,
        )
 
    def delete(self, path, **params):
        params["path"] = path
        return requests.delete(
            f"{self.base_url}/v1/disk/resources",
            headers=self.headers,
            params=params,
        )
 
 
@pytest.fixture(scope="session")
def disk_client():
    return DiskClient(BASE_URL, HEADERS)
 
 
def _unique_path(prefix, ext=""):
    return f"/{prefix}_{uuid.uuid4().hex[:8]}{ext}"
 
 
@pytest.fixture
def uploaded_file(disk_client):
    path = _unique_path("test_file", ".txt")
    content = b"pytest test content"
    resp = disk_client.upload_file(path, content, overwrite=True)
    assert resp.status_code == 201, f"Не удалось подготовить файл: {resp.text}"
 
    yield path, content
 
    disk_client.delete(path, permanently=True)
 
 
@pytest.fixture
def uploaded_folder(disk_client):
    path = _unique_path("test_dir")
    resp = disk_client.create_folder(path)
    assert resp.status_code == 201, f"Не удалось создать папку: {resp.text}"
 
    yield path
 
    disk_client.delete(path, permanently=True)
 
 
def md5_of(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def wait_until_status(get_func, expected_status, timeout=10, interval=1):
    deadline = time.time() + timeout
    last_response = None
    while time.time() < deadline:
        last_response = get_func()
        if last_response.status_code == expected_status:
            return last_response
        time.sleep(interval)
    return last_response