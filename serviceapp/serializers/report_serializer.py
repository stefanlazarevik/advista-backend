from datetime import date, timedelta, datetime

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from serviceapp.models import CountryReports, Reports


class CountryReportSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()
    country = serializers.CharField()

    def get_total_cost(self, report):
        try:
            return round(report['total_cost'], 2)
        except:
            return 0.00

    class Meta:
        model = CountryReports
        fields = ('country', 'country_code', 'total_cost')


class DailyReportSerializer(serializers.ModelSerializer):
    cost = serializers.SerializerMethodField()
    conversions = serializers.SerializerMethodField()
    clicks = serializers.SerializerMethodField()
    impressions = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    profit = serializers.SerializerMethodField()
    roi = serializers.SerializerMethodField()

    def get_cost(self, report):
        try:
            return round(report['spend__sum'], 2)
        except:
            return 0.00

    def get_revenue(self, report):
        try:
            return round(report['revenue__sum'], 2)
        except:
            return 0.00

    def get_profit(self, report):
        try:
            return round((report['revenue__sum'] - report['spend__sum']), 2)
        except:
            return 0.00

    def get_roi(self, report):
        try:
            return round((report['revenue__sum'] - report['spend__sum'])/report['spend__sum'] * 100, 2)
        except:
            return 0.00

    def get_conversions(self, report):
        try:
            return report['conversion__sum']
        except:
            return 0

    def get_clicks(self, report):
        try:
            return report['clicks__sum']
        except:
            return 0

    def get_impressions(self, report):
        try:
            return report['impressions__sum']
        except:
            return 0

    def get_products(self, report):
        try:
            return report['advertiser_id__count']
        except:
            return 0

    class Meta:
        model = Reports
        fields = ('cost', 'conversions', 'clicks', 'impressions', 'products', 'report_date', 'revenue', 'profit', 'roi')


# class DailyTotalReportSerializer(serializers.ModelSerializer):
#     total_cost = serializers.FloatField()
#     clicks = serializers.IntegerField()
#     conversion_rate = serializers.FloatField()
#     conversions = serializers.IntegerField()
#     cpm = serializers.FloatField()
#     cpc = serializers.FloatField()
#     ctr = serializers.FloatField()
#     cpa = serializers.FloatField()
#     revenue = serializers.FloatField()
#     impressions = serializers.IntegerField()
#     profit = serializers.FloatField()
#     roi = serializers.FloatField()
#
#     class Meta:
#         model = Reports
#         fields = ('report_date', 'total_cost', 'clicks', 'conversion_rate', 'conversions', 'cpm', 'cpc', 'ctr', 'cpa', 'impressions', 'revenue', 'profit', 'roi')