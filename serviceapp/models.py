from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.core.files.storage import FileSystemStorage
from PIL import Image
import uuid
import io
from datetime import datetime


def get_vertical_details():
    return {'name': "", 'category': "", 'domains': [], 'stats': [], 'source': [], 'url': []}


def get_creative_video():
    return {'id': "", 'url': "", 'filename': "", 'size': 0, 'type': ""}


def get_create_pixel():
    return {'label': "", 'url': ""}


def get_domain_for():
    return {'id': "", 'email': "", 'name': ""}


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
    updated_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, related_name='user_updated_by')
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


class TiktokBC(models.Model):
    bc_id = models.CharField(max_length=100, unique=True)
    bc_info = models.JSONField(default=dict)
    user_role = models.CharField(max_length=100, null=True)
    ext_user_role = models.JSONField(default=dict)

    class Meta:
        db_table = "tiktok_bc"


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
    description = models.CharField(max_length=255, null=True)
    promotion_center_city = models.CharField(max_length=100, null=True)
    license_url = models.CharField(max_length=255, null=True)
    contacter = models.CharField(max_length=255, null=True)
    owner_bc_id = models.CharField(max_length=100, null=True)
    promotion_area = models.CharField(max_length=255, null=True)
    license_city = models.CharField(max_length=255, null=True)
    license_no = models.CharField(max_length=255, null=True)
    currency = models.CharField(max_length=100, null=True)
    cellphone_number = models.CharField(max_length=100, null=True)
    telephone_number = models.CharField(max_length=100, null=True)
    email = models.CharField(max_length=100, null=True)
    promotion_center_province = models.CharField(max_length=100, null=True)
    company = models.CharField(max_length=255, null=True)
    language = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=100, null=True)
    status_code = models.CharField(choices=STATUS_CHOICE, max_length=32, default='active')
    balance = models.FloatField(null=True)
    country = models.CharField(max_length=100, null=True)
    timezone = models.CharField(max_length=100, null=True)
    license_province = models.CharField(max_length=100, null=True)
    advertiser_account_type = models.CharField(max_length=100, null=True)
    brand = models.CharField(max_length=100, null=True)
    industry = models.CharField(max_length=100, null=True)
    rejection_reason = models.TextField(null=True)
    create_time = models.BigIntegerField()
    address = models.TextField(null=True)
    tonic_campaign_name = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "advertisers"


class Reports(models.Model):
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')
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
    revenue = models.FloatField(default=0.0, null=True)

    class Meta:
        db_table = "reports"


class CountryReports(models.Model):
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')
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


class Campaigns(models.Model):
    campaign_id = models.CharField(max_length=100, unique=True)
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')
    is_new_structure = models.BooleanField(default=True)
    modify_time = models.DateTimeField(null=True)
    operation_status = models.CharField(max_length=255, null=True)
    objective = models.CharField(max_length=255, null=True)
    is_smart_performance_campaign = models.BooleanField(default=False)
    budget_mode = models.CharField(max_length=255, null=True)
    deep_bid_type = models.CharField(max_length=255, null=True)
    budget = models.FloatField(null=True)
    campaign_name = models.CharField(max_length=500, null=True)
    campaign_type = models.CharField(max_length=255, null=True)
    create_time = models.DateTimeField(null=True)
    rf_campaign_type = models.CharField(max_length=255, null=True)
    objective_type = models.CharField(max_length=255, null=True)
    secondary_status = models.CharField(max_length=255, null=True)
    roas_bid = models.FloatField(null=True)
    app_promotion_type = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "campaigns"


class CampaignReports(models.Model):
    campaign_id = models.ForeignKey(Campaigns, on_delete=models.SET_NULL, null=True, to_field='campaign_id',
                                    db_column='campaign_id')
    report_date = models.DateField()
    revenue = models.FloatField(default=0.0)
    tonic_campaign_id = models.CharField(max_length=100, null=True)
    tonic_campaign_name = models.CharField(max_length=500, null=True)
    clicks = models.IntegerField()
    keyword = models.TextField(null=True)
    adtitle = models.TextField(null=True)
    device = models.CharField(max_length=255, null=True)

    class Meta:
        db_table = "campaign_report"


class TonicCampaignReports(models.Model):
    report_date = models.DateField()
    revenue = models.FloatField(default=0.0)
    tonic_campaign_id = models.CharField(max_length=100, null=True)
    tonic_campaign_name = models.CharField(max_length=500, null=True)
    clicks = models.IntegerField()
    keyword = models.TextField(null=True)
    adtitle = models.TextField(null=True)
    device = models.CharField(max_length=255, null=True)
    subid1 = models.CharField(max_length=100, null=True)
    subid2 = models.CharField(max_length=100, null=True)
    subid3 = models.CharField(max_length=100, null=True)
    subid4 = models.CharField(max_length=100, null=True)
    network = models.CharField(max_length=100, null=True)
    site = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = "tonic_campaign_report"


class MediaBuyer(models.Model):
    media_buyer_id = models.CharField(max_length=100, unique=True)
    email = models.CharField(max_length=100, null=True)
    name = models.CharField(max_length=255, null=True)
    bc = models.JSONField(default=list, null=True)

    class Meta:
        db_table = "media_buyer"


class MediaBuyerAdvertiser(models.Model):
    media_buyer_id = models.ForeignKey(MediaBuyer, on_delete=models.SET_NULL, null=True, to_field='media_buyer_id',
                                       db_column='media_buyer_id')
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')

    class Meta:
        db_table = "media_buyer_advertiser"


class Vertical(models.Model):
    vertical_id = models.CharField(max_length=100, unique=True)
    details = models.JSONField(default=get_vertical_details)
    bc = models.JSONField(default=list, null=True)
    created_time = models.DateTimeField(null=True)

    class Meta:
        db_table = "vertical"


class VerticalAdvertiser(models.Model):
    vertical_id = models.ForeignKey(Vertical, on_delete=models.SET_NULL, null=True, to_field='vertical_id',
                                    db_column='vertical_id')
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')

    class Meta:
        db_table = "vertical_advertiser"


class Domains(models.Model):
    domain_id = models.CharField(max_length=100, unique=True)
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')
    domain_for = models.JSONField(default=get_domain_for, null=True)
    partner_url = models.TextField(null=True)
    source = models.CharField(max_length=100, null=True)
    stats = models.CharField(max_length=100, null=True)
    pixel_id = models.CharField(max_length=255, null=True)
    vertical = models.JSONField(default=list, null=True)
    country = models.CharField(max_length=100, null=True)
    creative_text = models.TextField(null=True)
    creative_video = models.JSONField(default=get_creative_video, null=True)
    language = models.CharField(max_length=100, null=True)
    network = models.JSONField(default=list, null=True)
    tracker_url = models.TextField(null=True)
    ticket_no = models.CharField(max_length=100, null=True)
    tiktok_account = models.JSONField(default=list, null=True)
    type = models.CharField(max_length=100, null=True)
    request_id = models.CharField(max_length=255, null=True)
    category = models.JSONField(default=list, null=True)
    create_pixel = models.JSONField(default=get_create_pixel, null=True)
    account_id = models.JSONField(default=list, null=True)
    status = models.JSONField(default=list, null=True)
    open_account = models.JSONField(default=list, null=True)
    account_button = models.JSONField(default=get_create_pixel, null=True)
    pixel_fire = models.JSONField(default=get_create_pixel, null=True)
    bc = models.JSONField(default=list, null=True)
    vertical_name = models.JSONField(default=list, null=True)
    name = models.JSONField(default=list, null=True)
    created_time = models.DateTimeField(null=True)

    class Meta:
        db_table = "domains"


class System1Revenue(models.Model):
    advertiser_id = models.ForeignKey(Advertisers, on_delete=models.SET_NULL, null=True, to_field='advertiser_id',
                                      db_column='advertiser_id')
    domain_id = models.ForeignKey(Domains, on_delete=models.SET_NULL, null=True, to_field='domain_id',
                                  db_column='domain_id')
    report_date = models.DateField()
    clicks = models.IntegerField()
    revenue = models.FloatField(default=0.0)
    revenue_per_click = models.FloatField(default=0.0)
    campaign = models.CharField(max_length=255, null=True)
    total_sessions = models.IntegerField(default=0)
    mobile_sessions = models.IntegerField(default=0)
    desktop_sessions = models.IntegerField(default=0)
    mobile_sessions_percentage = models.FloatField(default=0.0)
    distinct_ip = models.IntegerField(default=0)
    distinct_mobile_ip = models.IntegerField(default=0)
    distinct_desktop_ip = models.IntegerField(default=0)
    distinct_mobile_ip_percentage = models.FloatField(default=0.0)
    searches = models.IntegerField(default=0)
    revenue_per_session = models.FloatField(default=0.0)
    revenue_per_search = models.FloatField(default=0.0)
    revenue_per_ip = models.FloatField(default=0.0)
    click_per_session_percentage = models.FloatField(default=0.0)

    class Meta:
        db_table = "system1_revenue"


