from datetime import date, timedelta, datetime

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from serviceapp.models import Advertisers


class AdvertiserSerializer(serializers.ModelSerializer):
    total_cost = serializers.FloatField()
    clicks = serializers.IntegerField()
    conversion_rate = serializers.FloatField()
    conversions = serializers.IntegerField()
    cpm = serializers.FloatField()
    cpc = serializers.FloatField()
    ctr = serializers.FloatField()
    cpa = serializers.FloatField()
    revenue = serializers.FloatField()
    impressions = serializers.IntegerField()
    profit = serializers.FloatField()
    roi = serializers.FloatField()

    class Meta:
        model = Advertisers
        fields = ('id', 'advertiser_id', 'name', 'timezone', 'display_timezone', 'status', 'total_cost', 'clicks', 'conversion_rate', 'conversions', 'cpm', 'cpc', 'ctr', 'cpa', 'impressions', 'company', 'status_code', 'revenue', 'profit', 'roi')


class AdvertiserCSVSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()
    clicks = serializers.IntegerField()
    conversion_rate = serializers.SerializerMethodField()
    conversions = serializers.IntegerField()
    cpm = serializers.SerializerMethodField()
    cpc = serializers.SerializerMethodField()
    ctr = serializers.SerializerMethodField()
    cpa = serializers.SerializerMethodField()
    impressions = serializers.IntegerField()

    def get_total_cost(self, advertiser):
        try:
            return int(advertiser.total_cost)
        except:
            return 0

    def get_conversion_rate(self, advertiser):
        try:
            return round(advertiser.conversions/(advertiser.clicks/100), 2)
        except:
            return 0.00

    def get_ctr(self, advertiser):
        try:
            return round((advertiser.clicks / advertiser.impressions) * 100, 2)
        except:
            return 0.00

    def get_cpm(self, advertiser):
        try:
            return round((advertiser.total_cost / advertiser.impressions) * 1000, 2)
        except:
            return 0.00

    def get_cpc(self, advertiser):
        try:
            return round((advertiser.total_cost / advertiser.clicks), 2)
        except:
            return 0.00

    def get_cpa(self, advertiser):
        try:
            return round((advertiser.total_cost / advertiser.conversions), 2)
        except:
            return 0.00

    class Meta:
        model = Advertisers
        fields = ('name', 'company', 'total_cost', 'clicks', 'conversion_rate', 'conversions', 'cpm', 'cpc', 'ctr', 'cpa', 'impressions')