from adminsortable2.admin import SortableAdminBase, SortableTabularInline
from django.contrib import admin
from django.utils.html import format_html

from .models import Place, PlaceImage


class PlaceImageInline(SortableTabularInline):
    model = PlaceImage
    extra = 1
    readonly_fields = ("image_preview",)

    @admin.display(description="Превью")
    def image_preview(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="max-height: 100px; max-width: 100px; '
            'object-fit: contain; border: 1px solid #ccc; padding: 2px;" />',
            obj.image.url,
        )


@admin.register(Place)
class PlaceAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ("name", "lat", "lon")
    search_fields = ("name",)
    inlines = [PlaceImageInline]