from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from .models import Author, Genre, Book, BorrowRecord
from .serializers import (
    AuthorSerializer, GenreSerializer, BookSerializer,
    BorrowRecordSerializer
)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]  # только авторизованные могут изменять

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'title': ['icontains'],
        'authors': ['exact'],
        'genres': ['exact'],
        'publication_year': ['exact', 'gte', 'lte'],
    }

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class BorrowRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BorrowRecord.objects.all()
        return BorrowRecord.objects.filter(user=user)

    @action(detail=False, methods=['post'])
    def borrow(self, request):
        book_id = request.data.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        if book.available_copies < 1:
            return Response({'error': 'No copies available'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, не взял ли пользователь уже эту книгу и не вернул
        active_borrow = BorrowRecord.objects.filter(
            book=book, user=request.user, is_returned=False
        ).first()
        if active_borrow:
            return Response({'error': 'You already borrowed this book and have not returned it'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаём запись
        borrow = BorrowRecord.objects.create(book=book, user=request.user)
        book.available_copies -= 1
        book.save()

        serializer = self.get_serializer(borrow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        borrow = self.get_object()
        if borrow.is_returned:
            return Response({'error': 'Book already returned'}, status=status.HTTP_400_BAD_REQUEST)

        borrow.is_returned = True
        borrow.return_date = timezone.now().date()
        borrow.save()

        book = borrow.book
        book.available_copies += 1
        book.save()

        serializer = self.get_serializer(borrow)
        return Response(serializer.data)