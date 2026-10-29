from django.contrib import admin

from core.uploader.infra.uploader_django_app.models import Document, Image


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("description", "file", "uploaded_on")
    search_fields = ("description", "file")
    list_filter = ("uploaded_on",)
    ordering = ("-uploaded_on",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("description", "file", "uploaded_on")
    search_fields = ("description", "file")
    list_filter = ("uploaded_on",)
    ordering = ("-uploaded_on",)
