from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Author, Genre, Book, BorrowRecord


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True)
    genres = serializers.PrimaryKeyRelatedField(queryset=Genre.objects.all(), many=True)
    # Для отображения можно добавить строковые представления
    authors_names = serializers.StringRelatedField(source='authors', many=True, read_only=True)
    genres_names = serializers.StringRelatedField(source='genres', many=True, read_only=True)

    class Meta:
        model = Book
        fields = '__all__'

class BorrowRecordSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = BorrowRecord
        fields = '__all__'
        read_only_fields = ('borrow_date',)