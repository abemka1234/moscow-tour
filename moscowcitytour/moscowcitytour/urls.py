"""
URL configuration for moscowcitytour project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.main_view, name="main"),
    path(
        "places/<int:placeId>/",
        views.parse_place_details,
        name="parse_place_details",
    ),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
] + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    