from django.contrib import admin

from core.uploader.models import Document, Image

admin.site.register(Image)
admin.site.register(Document)
