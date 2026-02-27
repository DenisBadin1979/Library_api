from django.db import models

from users.models import User


class Author(models.Model):
    name = models.CharField(max_length=200, verbose_name="Наименование автора")
    bio = models.TextField(verbose_name="Кратко об авторе", blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Жанр книг")

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название произведения")
    authors = models.ManyToManyField(Author, related_name="books", verbose_name="Автор")
    genres = models.ManyToManyField(Genre, related_name="books", verbose_name="Жанр")
    isbn = models.CharField(
        max_length=13,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Международный стандартный книжный номер (ISBN)",
    )
    available_copies = models.IntegerField(
        default=1, verbose_name="Доступно экземпляров"
    )

    def __str__(self):
        return self.title


class BorrowRecord(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrow_records"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="borrow_records"
    )
    borrow_date = models.DateField(auto_now_add=True, verbose_name="Дата выдачи книги")
    return_date = models.DateField(
        null=True, blank=True, verbose_name="Дата возврата книги"
    )
    is_returned = models.BooleanField(
        default=False, verbose_name="ОТметка о возврате"
    )  # для удобства

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.borrow_date})"
