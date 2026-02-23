from django.contrib import admin


from library.models import Author, Genre, Book, BorrowRecord

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(BorrowRecord)
