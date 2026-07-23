# disk-api-tests
Проект содержит API-тесты для Яндекс Диска

Стек:
Python3
Pytest
requests

## Установка:

```bash 
git clone https://github.com/ViktoriaAl/disk-api-tests.git
cd disk-api-tests

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## Настройка токена
```bash
export YANDEX_DISK_TOKEN=токен
```

## Запуск тестов:
```bash
pytest
```
