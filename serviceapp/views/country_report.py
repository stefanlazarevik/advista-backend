import json

from django.db.models import Sum
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers, Reports, CountryReports
from rest_framework.decorators import api_view

from serviceapp.serializers.report_serializer import CountryReportSerializer
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper, UserPermissions
from datetime import datetime, timedelta, date
import pycountry


class CountryReportView(APIView):
    # permission_classes = (UserPermissions,)

    # def get(self, request):
    #     response = {}
    #     try:
    #         start_date = request.GET.get('start_date')
    #         end_date = request.GET.get('end_date')
    #         country_reports = CountryReports.objects.filter(report_date__gte=start_date, report_date__lte=end_date).values('country').annotate(total_cost=Sum('spend'), ).exclude(country=None).order_by('-total_cost')[:5]
    #         serializer = CountryReportSerializer(country_reports, many=True)
    #         response["success"] = True
    #         response["data"] = serializer.data
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @api_view(["get"])
    def get_daily_country_report(request):
        response = {}
        try:
            report_list = []
            today = datetime.now().date()
            # today = request.GET.get('today')
            if not CountryReports.objects.filter(report_date=today).exists():
                tiktok_info = TiktokInfo.objects.get(id=1)
                access_token = tiktok_info.access_token
                advertisers = Advertisers.objects.all()
                for advertiser in advertisers:
                    daily_report = CountryReportView.get_report_by_advertiser(request, advertiser.advertiser_id, access_token, today)
                    if 'data' in daily_report:
                        report_data = daily_report['data']
                        for report in report_data:
                            data = report['metrics']
                            country_code = report['dimensions']['country_code']
                            data['country_code'] = None
                            data['country'] = None
                            if country_code != 'None':
                                data['country_code'] = country_code
                                country = pycountry.countries.get(alpha_2=country_code)
                                data['country'] = country.name
                                report_dict = {
                                    "advertiser_id": advertiser,
                                    "report_date": today,
                                    "cost_per_conversion": data['cost_per_conversion'],
                                    "ctr": data['ctr'],
                                    "cpc": data['cpc'],
                                    "spend": data['spend'],
                                    "impressions": data['impressions'],
                                    "clicks": data['clicks'],
                                    "cpm": data['cpm'],
                                    "conversion": data['conversion'],
                                    "conversion_rate": data['conversion_rate'],
                                    "reach": data['reach'],
                                    "country": data['country'],
                                    "country_code": data['country_code']
                                }
                                report_list.append(CountryReports(**report_dict))
                if len(report_list) > 0:
                    CountryReports.objects.bulk_create(report_list)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_report_by_advertiser(request, advertiser_id, access_token, today):
        response = {}
        try:
            # Args in JSON format
            path = "/report/integrated/get/"
            metrics_list = ["spend", "impressions", "cpc", "cpm", "ctr", "reach", "clicks", "stat_cost", "show_cnt", "click_cnt", "time_attr_convert_cnt", "time_attr_conversion_cost", "time_attr_conversion_rate"]
            metrics = json.dumps(metrics_list)
            data_level = 'AUCTION_ADVERTISER'
            end_date = today
            start_date = today
            report_type = 'BASIC'
            dimensions_list = ["country_code"]
            dimensions = json.dumps(dimensions_list)

            # Args in JSON format
            my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
                metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
            reports = tiktok_get(my_args, path, access_token)
            if 'list' in reports['data'] and len(reports['data']['list']) > 0:
                response["data"] = reports['data']['list']
            response["success"] = True
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response



