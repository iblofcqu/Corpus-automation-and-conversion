"""
text_extraction应用URL配置
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FileUploadView,
    FileViewSet,
    ProjectViewSet,
    FileDeleteView,
    FileUpdateView,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"files", FileViewSet, basename="file")

urlpatterns = [
    path(
        "files/<int:file_id>/",
        FileDeleteView.as_view(),
        name="delete-file",
    ),
    path(
        "files/<int:file_id>/",
        FileUpdateView.as_view(),
        name="put-result",
    ),
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("", include(router.urls)),
]
