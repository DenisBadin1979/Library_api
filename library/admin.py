from django.contrib import admin

from library.models import Author, Book, BorrowRecord, Genre

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(BorrowRecord)
