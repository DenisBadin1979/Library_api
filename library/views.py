from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    inline_serializer,
)
from rest_framework import filters, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Author, Book, BorrowRecord, Genre
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    BorrowRecordSerializer,
    GenreSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="Список авторов", tags=["Авторы"]),
    retrieve=extend_schema(summary="Детальная информация об авторе", tags=["Авторы"]),
    create=extend_schema(summary="Добавить автора", tags=["Авторы"]),
    update=extend_schema(summary="Изменить автора полностью", tags=["Авторы"]),
    partial_update=extend_schema(summary="Изменить автора частично", tags=["Авторы"]),
    destroy=extend_schema(summary="Удалить автора", tags=["Авторы"]),
)
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]  # только авторизованные могут изменять


@extend_schema_view(
    list=extend_schema(summary="Список жанров", tags=["Жанры"]),
    retrieve=extend_schema(summary="Детальная информация о жанре", tags=["Жанры"]),
    create=extend_schema(summary="Добавить жанр", tags=["Жанры"]),
    update=extend_schema(summary="Изменить жанр полностью", tags=["Жанры"]),
    partial_update=extend_schema(summary="Изменить жанр частично", tags=["Жанры"]),
    destroy=extend_schema(summary="Удалить жанр", tags=["Жанры"]),
)
class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = {
        "title": ["icontains"],
        "authors": ["exact"],
        "genres": ["exact"],
    }
    search_fields = ["title", "authors__name", "genres__name", "isbn"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Список книг с фильтрацией и поиском",
        description="Получение списка книг с возможностью фильтрации по названию, автору, жанру и поиском по ISBN.",
        parameters=[
            OpenApiParameter(
                name="title__icontains",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Часть названия книги",
            ),
            OpenApiParameter(
                name="authors",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ID автора",
            ),
            OpenApiParameter(
                name="genres",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ID жанра",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Поиск по названию, имени автора, жанру или ISBN",
            ),
        ],
        tags=["Книги"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class BorrowRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BorrowRecord.objects.all()
        return BorrowRecord.objects.filter(user=user)

    @extend_schema(
        summary="Взять книгу",
        description="Позволяет авторизованному пользователю взять книгу, уменьшая количество доступных копий.",
        request=inline_serializer(
            name="BorrowRequest",
            fields={"book_id": serializers.IntegerField(help_text="ID книги")},
        ),
        responses={
            201: BorrowRecordSerializer,
            400: inline_serializer(
                name="BorrowError", fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="NotFound", fields={"error": serializers.CharField()}
            ),
        },
        tags=["Выдачи"],
    )
    @action(detail=False, methods=["post"])
    def borrow(self, request):
        book_id = request.data.get("book_id")
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response(
                {"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if book.available_copies < 1:
            return Response(
                {"error": "No copies available"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, не взял ли пользователь уже эту книгу и не вернул
        active_borrow = BorrowRecord.objects.filter(
            book=book, user=request.user, is_returned=False
        ).first()
        if active_borrow:
            return Response(
                {"error": "You already borrowed this book and have not returned it"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаём запись
        borrow = BorrowRecord.objects.create(book=book, user=request.user)
        book.available_copies -= 1
        book.save()

        serializer = self.get_serializer(borrow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Вернуть книгу",
        description="Помечает запись о выдаче как возвращённую и увеличивает количество доступных копий.",
        request=None,  # тело не требуется
        responses={
            200: BorrowRecordSerializer,
            400: inline_serializer(
                name="ReturnError", fields={"error": serializers.CharField()}
            ),
        },
        tags=["Выдачи"],
    )
    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        borrow = self.get_object()
        if borrow.is_returned:
            return Response(
                {"error": "Book already returned"}, status=status.HTTP_400_BAD_REQUEST
            )

        borrow.is_returned = True
        borrow.return_date = timezone.now().date()
        borrow.save()

        book = borrow.book
        book.available_copies += 1
        book.save()

        serializer = self.get_serializer(borrow)
        return Response(serializer.data)
