from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from library.models import Author, Book, BorrowRecord, Genre

User = get_user_model()


class BaseTestCase(TestCase):
    """Базовый класс с общими настройками и вспомогательными методами."""

    @classmethod
    def setUpTestData(cls):
        # Создаём обычного пользователя и админа (is_staff)
        cls.user = User.objects.create_user(email="user@example.com", password="pass")
        cls.admin = User.objects.create_superuser(
            email="admin@example.com", password="admin"
        )

        # Авторы, жанры, книги
        cls.author1 = Author.objects.create(
            name="Лев Толстой", bio="Война и мир", birth_date="1828-09-09"
        )
        cls.author2 = Author.objects.create(
            name="Фёдор Достоевский",
            bio="Преступление и наказание",
            birth_date="1821-11-11",
        )

        cls.genre1 = Genre.objects.create(name="Роман")
        cls.genre2 = Genre.objects.create(name="Драма")

        cls.book1 = Book.objects.create(
            title="Война и мир", isbn="1234567890123", available_copies=5
        )
        cls.book1.authors.add(cls.author1)
        cls.book1.genres.add(cls.genre1, cls.genre2)

        cls.book2 = Book.objects.create(
            title="Преступление и наказание", isbn="9876543210987", available_copies=2
        )
        cls.book2.authors.add(cls.author2)
        cls.book2.genres.add(cls.genre1)

    def setUp(self):
        self.client = APIClient()


class AuthorViewSetTest(BaseTestCase):
    """Тесты для AuthorViewSet."""

    def test_list_authors_unauthenticated(self):
        """Неавторизованный пользователь не может получить список авторов (требуется аутентификация)."""
        response = self.client.get("/author/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authors_authenticated(self):
        """Авторизованный пользователь может получить список авторов."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/author/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_author(self):
        """Создание автора доступно только авторизованному пользователю."""
        data = {"name": "Новый автор", "bio": "Биография", "birth_date": "2000-01-01"}
        # без аутентификации
        response = self.client.post("/author/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # с аутентификацией
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/author/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Author.objects.count(), 3)

    def test_update_author(self):
        """Обновление автора доступно авторизованному."""
        self.client.force_authenticate(user=self.user)
        data = {"name": "Толстой Л.Н."}
        response = self.client.patch(f"/author/{self.author1.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author1.refresh_from_db()
        self.assertEqual(self.author1.name, "Толстой Л.Н.")


class GenreViewSetTest(BaseTestCase):
    """Тесты для GenreViewSet."""

    def test_list_genres_unauthenticated(self):
        response = self.client.get("/genre/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_genres_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/genre/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_genre(self):
        data = {"name": "Фантастика"}
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/genre/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Genre.objects.count(), 3)


class BookViewSetTest(BaseTestCase):
    """Тесты для BookViewSet."""

    def test_list_books_allow_any(self):
        """Неавторизованный может просматривать список книг."""
        response = self.client.get("/book/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_book_allow_any(self):
        response = self.client.get(f"/book/{self.book1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.book1.title)

    def test_create_book_authenticated_only(self):
        data = {
            "title": "Новая книга",
            "isbn": "1112223334445",
            "authors": [self.author1.id, self.author2.id],
            "genres": [self.genre1.id],
            "available_copies": 3,
        }
        # без аутентификации
        response = self.client.post("/book/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # с аутентификацией
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/book/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)

    def test_filter_books_by_title(self):
        response = self.client.get(
            "/book/", {"title__icontains": "война"}
        )  # было {'title': 'война'}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Война и мир")

    def test_filter_books_by_author(self):
        response = self.client.get("/book/", {"authors": self.author1.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Война и мир")

    def test_filter_books_by_genre(self):
        response = self.client.get("/book/", {"genres": self.genre2.id})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Война и мир")

    def test_search_books(self):
        response = self.client.get("/book/", {"search": "преступление"})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Преступление и наказание")


class BorrowRecordViewSetTest(BaseTestCase):
    """Тесты для BorrowRecordViewSet и кастомных действий borrow/return."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_list_borrow_records_user_sees_only_own(self):
        """Обычный пользователь видит только свои записи."""
        # Создаём записи для разных пользователей
        BorrowRecord.objects.create(book=self.book1, user=self.user)
        BorrowRecord.objects.create(book=self.book2, user=self.admin)

        response = self.client.get("/borrowrecord/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["book"], self.book1.id)

    def test_admin_sees_all_borrow_records(self):
        """Администратор видит все записи."""
        self.client.force_authenticate(user=self.admin)
        BorrowRecord.objects.create(book=self.book1, user=self.user)
        BorrowRecord.objects.create(book=self.book2, user=self.admin)

        response = self.client.get("/borrowrecord/")
        self.assertEqual(len(response.data), 2)

    def test_borrow_book_success(self):
        """Успешное взятие книги."""
        initial_copies = self.book1.available_copies
        response = self.client.post("/borrowrecord/borrow/", {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем создание записи
        self.assertEqual(BorrowRecord.objects.count(), 1)
        borrow = BorrowRecord.objects.first()
        self.assertEqual(borrow.book, self.book1)
        self.assertEqual(borrow.user, self.user)
        self.assertFalse(borrow.is_returned)
        self.assertIsNone(borrow.return_date)

        # Проверяем уменьшение количества копий
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.available_copies, initial_copies - 1)

    def test_borrow_book_not_found(self):
        """Попытка взять несуществующую книгу."""
        response = self.client.post("/borrowrecord/borrow/", {"book_id": 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Book not found")

    def test_borrow_book_no_copies(self):
        """Попытка взять книгу с нулевым количеством доступных копий."""
        self.book1.available_copies = 0
        self.book1.save()
        response = self.client.post("/borrowrecord/borrow/", {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "No copies available")

    def test_borrow_already_borrowed_not_returned(self):
        """Пользователь не может взять ту же книгу, если не вернул предыдущую."""
        BorrowRecord.objects.create(book=self.book1, user=self.user, is_returned=False)
        response = self.client.post("/borrowrecord/borrow/", {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "You already borrowed this book and have not returned it",
        )

    def test_return_book_success(self):
        """Успешный возврат книги."""
        borrow = BorrowRecord.objects.create(
            book=self.book1, user=self.user, is_returned=False
        )
        initial_copies = self.book1.available_copies

        response = self.client.post(f"/borrowrecord/{borrow.id}/return_book/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        borrow.refresh_from_db()
        self.assertTrue(borrow.is_returned)
        self.assertIsNotNone(borrow.return_date)

        self.book1.refresh_from_db()
        self.assertEqual(self.book1.available_copies, initial_copies + 1)

    def test_return_book_already_returned(self):
        """Попытка вернуть уже возвращённую книгу."""
        borrow = BorrowRecord.objects.create(
            book=self.book1, user=self.user, is_returned=True
        )
        response = self.client.post(f"/borrowrecord/{borrow.id}/return_book/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Book already returned")

    def test_return_book_unauthorized_user(self):
        """Пользователь не может вернуть чужую книгу (проверка прав доступа)."""
        borrow = BorrowRecord.objects.create(
            book=self.book1, user=self.admin, is_returned=False
        )
        # Пытаемся вернуть от имени обычного пользователя
        response = self.client.post(f"/borrowrecord/{borrow.id}/return_book/")
        # Должен быть 404, так как get_queryset для обычного пользователя не включает эту запись
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PermissionsTest(BaseTestCase):
    """Дополнительные тесты прав доступа."""

    def test_author_update_delete_require_auth(self):
        """Обновление/удаление автора требует аутентификации."""
        # DELETE без аутентификации
        response = self.client.delete(f"/author/{self.author1.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # DELETE с аутентификацией
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/author/{self.author1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_book_update_delete_require_auth(self):
        """Обновление/удаление книги требует аутентификации."""
        # PATCH без аутентификации
        response = self.client.patch(f"/book/{self.book1.id}/", {"title": "New"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/book/{self.book1.id}/", {"title": "New"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.title, "New")

    def test_borrow_action_requires_auth(self):
        """Действие borrow требует аутентификации."""
        self.client.logout()
        response = self.client.post("/borrowrecord/borrow/", {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
