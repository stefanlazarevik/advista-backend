from django.db import models
from django.contrib.auth.models import AbstractUser
import io
from datetime import datetime


class Users(AbstractUser):
    USERMODE_CHOICE = (
        ('1', 'Customer'),
        ('2', 'Admin')
    )

    phone = models.CharField(max_length=20, null=True)
    email_verification_token = models.CharField(max_length=100, null=True)
    email_expired_at = models.DateField(null=True)
    user_mode = models.CharField(choices=USERMODE_CHOICE, max_length=32, default='1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # USERNAME_FIELD = 'email'

    def get_full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    class Meta:
        db_table = "users"