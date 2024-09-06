from rest_framework import mixins, parsers, viewsets

from core.uploader.infra.uploader_django_app.models import Document, Image
from core.uploader.infra.uploader_django_app.serializers import DocumentUploadSerializer, ImageUploadSerializer


class CreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    pass


class DocumentUploadViewSet(CreateViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]


class ImageUploadViewSet(CreateViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
