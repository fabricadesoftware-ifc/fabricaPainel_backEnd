import mimetypes
import uuid
from typing import TYPE_CHECKING

from django.db import models

from core.uploader.domain.utils.files import get_content_type


def image_file_path(image, _):
    extension = ".jpg"
    return f"images/{image.public_id}{extension}"


class Image(models.Model):
    if TYPE_CHECKING:
        id: int

    attachment_key = models.UUIDField(
        max_length=255,
        default=uuid.uuid4,
        unique=True,
        help_text=(
            "Used to attach the image to another object. "
            "Cannot be used to retrieve the image file."
        ),
    )
    public_id = models.UUIDField(
        max_length=255,
        default=uuid.uuid4,
        unique=True,
        help_text=(
            "Used to retrieve the image itself. "
            "Should not be readable until the image is attached to another object."
        ),
    )
    file = models.ImageField(upload_to=image_file_path, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "(%s - %s)" % (self.description, self.attachment_key)

    @property
    def url(self):
        return self.file.url
