from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from PIL import Image
import io
from datetime import datetime


def get_upload_path(instance, filename):
    """ creates unique-Path & filename for upload """
    ext = filename.split('.')[-1]
    image = Image.open(instance.photo)
    old_image = image
    output_image = io.BytesIO()
    image.save(output_image, old_image.format)
    filename = "%s.%s" % (instance.photo.name, ext)
    d = datetime.today()
    filename_with_path = 'public/images/' + d.strftime('%Y') + "/" + d.strftime('%m') + "/" + filename
    return filename_with_path


class Users(AbstractUser):
    phone = models.CharField(max_length=20, null=True)
    avatar = models.FileField(null=True, upload_to='avatar/',
                            validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'svg', 'jpeg'])],
                            storage=FileSystemStorage())
    avatar_thumb = models.FileField(null=True, upload_to='avatar/',
                                  validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'svg', 'jpeg'])],
                                  storage=FileSystemStorage())
    email_verification_token = models.CharField(max_length=100, null=True)
    email_expired_at = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # USERNAME_FIELD = 'email'

    def get_full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    class Meta:
        db_table = "users"