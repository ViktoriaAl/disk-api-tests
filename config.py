import os
 
BASE_URL = "https://cloud-api.yandex.net"

TOKEN = os.environ.get("YANDEX_DISK_TOKEN")
 
if not TOKEN:
    raise RuntimeError(
        "Токен не найден. Установите переменную окружения YANDEX_DISK_TOKEN"
    )
 
HEADERS = {
    "Authorization": f"OAuth {TOKEN}",
    "Content-Type": "application/json",
}
 