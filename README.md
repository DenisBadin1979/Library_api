Library API
REST API для управления библиотекой. Проект разработан на Django Rest Framework с использованием JWT аутентификации. Позволяет управлять книгами, авторами, жанрами, а также отслеживать выдачу книг пользователям.

Технологии
Python 3.11

Django 4.2

Django REST Framework

PostgreSQL

Docker, Docker Compose

JWT (аутентификация через djangorestframework-simplejwt)

drf-spectacular (автодокументация OpenAPI)

Установка и запуск
Локальный запуск (без Docker)
Клонируйте репозиторий:

bash
git clone <url-репозитория>
cd library_api
Создайте и активируйте виртуальное окружение:

bash
python -m venv .venv
source .venv/bin/activate   # для Linux/Mac
.venv\Scripts\activate      # для Windows
Установите зависимости:

bash
pip install -r requirements.txt
Создайте файл .env в корне проекта и укажите переменные окружения (пример в .env.example):

text
DB_NAME=library_db
DB_USER=library_user
DB_PASSWORD=securepassword
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=True
Выполните миграции:

bash
python manage.py migrate
Создайте суперпользователя:

bash
python manage.py createsuperuser
Запустите сервер:

bash
python manage.py runserver
Запуск через Docker
Убедитесь, что установлены Docker и Docker Compose.

Скопируйте .env.example в .env и при необходимости отредактируйте.

Выполните сборку и запуск контейнеров:

bash
docker-compose up --build
Примените миграции внутри контейнера:

bash
docker-compose exec web python manage.py migrate
Создайте суперпользователя:

bash
docker-compose exec web python manage.py createsuperuser
После запуска API будет доступно по адресу http://localhost:8000.

Использование API
Аутентификация
Для доступа к защищённым эндпоинтам необходимо получить JWT токен.

Регистрация пользователя
POST /api/users/register/
Тело запроса:

json
{
    "email": "user@example.com",
    "password": "securepassword",
    "first_name": "Иван",
    "last_name": "Иванов"
}
Получение токена
POST /api/token/
Тело запроса:

json
{
    "email": "user@example.com",
    "password": "securepassword"
}
Ответ:

json
{
    "refresh": "refresh-token",
    "access": "access-token"
}
Обновление токена
POST /api/token/refresh/
Тело запроса:

json
{
    "refresh": "refresh-token"
}
При запросах к защищённым эндпоинтам добавляйте заголовок:

text
Authorization: Bearer <access-token>
Основные эндпоинты
Ресурс	Метод	Эндпоинт	Описание	Доступ
Авторы	GET	/api/authors/	Список всех авторов	Только авторизованные
POST	/api/authors/	Создание автора	Только авторизованные
GET	/api/authors/{id}/	Детали автора	Только авторизованные
PUT	/api/authors/{id}/	Полное обновление автора	Только авторизованные
PATCH	/api/authors/{id}/	Частичное обновление автора	Только авторизованные
DELETE	/api/authors/{id}/	Удаление автора	Только авторизованные
Жанры	GET	/api/genres/	Список жанров	Только авторизованные
POST	/api/genres/	Создание жанра	Только авторизованные
Книги	GET	/api/books/	Список книг (с фильтрацией)	Публичный
POST	/api/books/	Добавление книги	Только авторизованные
GET	/api/books/{id}/	Детали книги	Публичный
PUT	/api/books/{id}/	Обновление книги	Только авторизованные
PATCH	/api/books/{id}/	Частичное обновление	Только авторизованные
DELETE	/api/books/{id}/	Удаление книги	Только авторизованные
Выдача книг	GET	/api/borrowrecords/	Список выдач (только свои)	Только авторизованные
POST	/api/borrowrecords/borrow/	Взять книгу	Только авторизованные
POST	/api/borrowrecords/{id}/return_book/	Вернуть книгу	Только авторизованные
Фильтрация и поиск книг
Фильтрация по названию (частичное совпадение):
GET /api/books/?title__icontains=война

Фильтрация по автору (точное совпадение ID):
GET /api/books/?authors=1

Фильтрация по жанру (точное совпадение ID):
GET /api/books/?genres=2

Полнотекстовый поиск (по названию, имени автора, названию жанра, ISBN):
GET /api/books/?search=преступление

Примеры запросов
Взять книгу
bash
curl -X POST http://localhost:8000/api/borrowrecords/borrow/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1}'
Вернуть книгу
bash
curl -X POST http://localhost:8000/api/borrowrecords/1/return_book/ \
  -H "Authorization: Bearer <access-token>"
Документация API
После запуска проекта автодокументация в формате OpenAPI доступна по адресу:

Swagger UI: http://localhost:8000/api/schema/swagger-ui/

ReDoc: http://localhost:8000/api/schema/redoc/

Схема в формате JSON: http://localhost:8000/api/schema/

Документация генерируется автоматически с помощью drf-spectacular.

Тестирование
Для запуска тестов выполните:

bash
python manage.py test
Для проверки покрытия (если установлен coverage):

bash
coverage run --source='.' manage.py test
coverage report