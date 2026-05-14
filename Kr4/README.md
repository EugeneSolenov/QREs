# Контрольная работа №4

Решение заданий из файла `Контрольная работа №4. Технологии разработки серверных приложений.pdf`.

## Что реализовано

- FastAPI-приложение в `app/main.py`.
- SQLAlchemy-модель `Product` и SQLite-база.
- Alembic с двумя миграциями:
  - `0001_create_products.py` создает таблицу `products`;
  - `0002_add_product_description.py` добавляет обязательное поле `description`.
- Скрипт `tools/seed_products.py`, который добавляет две записи в `products`.
- Пользовательские исключения и обработчики ошибок.
- Пользовательский обработчик ошибок валидации `RequestValidationError`.
- Синхронные тесты через `TestClient`.
- Асинхронные тесты через `pytest-asyncio`, `httpx.AsyncClient`, `ASGITransport` и `Faker`.

## Установка

```powershell
py -m pip install -r requirements.txt
```

## Миграции и тестовые данные

```powershell
py -m alembic upgrade head
py tools/seed_products.py
```

После выполнения команд будет создана локальная SQLite-база `products.db`, а таблица `products` будет содержать две записи.

## Запуск приложения

```powershell
py -m uvicorn app.main:app --reload
```

Документация API будет доступна по адресу:

```text
http://127.0.0.1:8000/docs
```

## Проверка

```powershell
py -m pytest -q
```

## Основные endpoints

- `GET /errors/condition?value=-1` - демонстрация пользовательского исключения с кодом `400`.
- `GET /errors/resources/999` - демонстрация пользовательского исключения с кодом `404`.
- `POST /validation/users` - проверка пользовательских данных через Pydantic и кастомный обработчик ошибок валидации.
- `POST /users` - создание пользователя в in-memory хранилище.
- `GET /users/{user_id}` - получение пользователя.
- `DELETE /users/{user_id}` - удаление пользователя.
- `GET /products` - чтение записей из таблицы `products`.
"# kr4" 
