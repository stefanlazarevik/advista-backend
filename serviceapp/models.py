from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from PIL import Image
import uuid
import io
from datetime import datetime


class Users(AbstractUser):
    USERMODE_CHOICE = (
        ('1', 'Customer'),
        ('2', 'Admin')
    )
    # uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, null=True)
    email_verification_token = models.CharField(max_length=100, null=True)
    email_expired_at = models.DateTimeField(null=True)
    is_verified = models.BooleanField(default=False)
    user_mode = models.CharField(choices=USERMODE_CHOICE, max_length=32, default='1')
    avatar = models.FileField(null=True, upload_to='avatar/',
                              validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'svg', 'jpeg'])],
                              storage=FileSystemStorage())
    avatar_thumb = models.FileField(null=True, upload_to='avatar/',
                                    validators=[
                                        FileExtensionValidator(allowed_extensions=['jpg', 'png', 'svg', 'jpeg'])],
                                    storage=FileSystemStorage())
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, related_name='user_created_by')
    updated_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True,  related_name='user_updated_by')
    updated_at = models.DateTimeField(auto_now=True)

    # USERNAME_FIELD = 'email'

    def get_full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    class Meta:
        db_table = "users"


class TiktokInfo(models.Model):
    bc_id = models.CharField(max_length=100, unique=True)
    app_id = models.CharField(max_length=100)
    secret = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    bc_info = models.JSONField(default=dict)

    class Meta:
        db_table = "tiktok_info"


class Advertisers(models.Model):
    STATUS_CHOICE = (
        ('active', 'Active'),
        ('disabled', 'Disabled'),
        ('review', 'Review'),
        ('verification', 'Verification'),
        ('failed', 'Failed'),
        ('limit', 'Limit')
    )

    advertiser_id = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=100, null=True)
    display_timezone = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=100, null=True)
    promotion_center_city = models.CharField(max_length=100, null=True)
    license_url = models.CharField(max_length=100, null=True)
    contacter = models.CharField(max_length=100, null=True)
    owner_bc_id = models.CharField(max_length=100, null=True)
    promotion_area = models.CharField(max_length=100, null=True)
    license_city = models.CharField(max_length=100, null=True)
    license_no = models.CharField(max_length=100, null=True)
    currency = models.CharField(max_length=100, null=True)
    cellphone_number = models.CharField(max_length=100, null=True)
    telephone_number = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=100, null=True)
    promotion_center_province = models.CharField(max_length=100, null=True)
    company = models.CharField(max_length=255, null=True)
    language = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=100, null=True)
    status_code = models.CharField(choices=STATUS_CHOICE, max_length=32, default='active')
    balance = models.FloatField(null=True)
    country = models.CharField(max_length=100, null=True)
    timezone = models.CharField(max_length=100, null=True)
    license_province = models.CharField(max_length=100, null=True)
    advertiser_account_type = models.CharField(max_length=100, null=True)
    brand = models.CharField(max_length=100, null=True)
    industry = models.CharField(max_length=100, null=True)
    rejection_reason = models.CharField(max_length=100, null=True)
    create_time = models.BigIntegerField()
    address = models.TextField(null=True)

    class Meta:
        db_table = "advertisers"


class Reports(models.Model):
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id', db_column='advertiser_id')
    real_time_conversion = models.IntegerField(null=True)
    cost_per_conversion = models.FloatField(null=True)
    cpm = models.FloatField(null=True)
    clicks = models.IntegerField(null=True)
    ctr = models.FloatField(null=True)
    conversion = models.IntegerField(null=True)
    skan_conversion_rate = models.FloatField(null=True)
    skan_conversion = models.IntegerField(null=True)
    conversion_rate = models.FloatField(null=True)
    real_time_cost_per_conversion = models.FloatField(null=True)
    skan_cost_per_conversion = models.FloatField(null=True)
    impressions = models.IntegerField(null=True)
    spend = models.FloatField(null=True)
    cpc = models.FloatField(null=True)
    report_date = models.DateField()

    class Meta:
        db_table = "reports"


class CountryReports(models.Model):
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id', db_column='advertiser_id')
    country_code = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=100, null=True)
    cost_per_conversion = models.FloatField(null=True)
    cpm = models.FloatField(null=True)
    clicks = models.IntegerField(null=True)
    ctr = models.FloatField(null=True)
    conversion = models.IntegerField(null=True)
    conversion_rate = models.FloatField(null=True)
    impressions = models.IntegerField(null=True)
    spend = models.FloatField(null=True)
    cpc = models.FloatField(null=True)
    reach = models.IntegerField(null=True)
    report_date = models.DateField()

    class Meta:
        db_table = "country_reports"


class Partners(models.Model):
    name = models.CharField(max_length=255, null=True)
    partner_id = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "partners"
