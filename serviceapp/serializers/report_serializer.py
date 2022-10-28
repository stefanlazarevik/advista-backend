from datetime import date, timedelta, datetime

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from serviceapp.models import CountryReports


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