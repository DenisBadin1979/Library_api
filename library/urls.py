from django.urls import path
from rest_framework.routers import DefaultRouter

from library.apps import LibraryConfig
from library.views import AuthorViewSet, GenreViewSet, BookViewSet, BorrowRecordViewSet

app_name = LibraryConfig.name

router = DefaultRouter()
router.register(r"author", AuthorViewSet, basename="author")
router.register(r"genre", GenreViewSet, basename="genre")
router.register(r"book", BookViewSet, basename="book")
router.register(r"borrowrecord", BorrowRecordViewSet, basename="borrowrecord")

urlpatterns = []

urlpatterns += router.urls