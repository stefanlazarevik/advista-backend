import json
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers, Reports
from rest_framework.decorators import api_view
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper
from datetime import datetime, timedelta, date


class ReportView(APIView):

    # def get(self, request):
    #     serializer = UserSerializer(request.user)
    #     return Response(data=serializer.data, status=status.HTTP_200_OK)

    @api_view(["get"])
    def get_daily_report(request):
        response = {}
        try:
            report_list = []
            # today = datetime.now().date()
            today = request.GET.get('today')
            if not Reports.objects.filter(report_date=today).exists():
                tiktok_info = TiktokInfo.objects.get(id=1)
                access_token = tiktok_info.access_token
                advertisers = Advertisers.objects.all()
                for advertiser in advertisers:
                    daily_report = ReportView.get_report_by_advertiser(request, advertiser.advertiser_id, access_token, today)
                    if 'data' in daily_report:
                        # daily_report['data']['advertiser_id'] = advertiser
                        # daily_report['data']['report_date'] = daily_report['report_date']
                        report_data = daily_report['data']
                        report_dict = {
                            "advertiser_id": advertiser,
                            "report_date": today,
                            "clicks": report_data['clicks'],
                            "conversion": report_data['conversion'],
                            "skan_conversion": report_data['skan_conversion'],
                            "cpc": report_data['cpc'],
                            "cost_per_conversion": report_data['cost_per_conversion'],
                            "conversion_rate": report_data['conversion_rate'],
                            "skan_cost_per_conversion": report_data['skan_cost_per_conversion'],
                            "spend": report_data['spend'],
                            "skan_conversion_rate": report_data['skan_conversion_rate'],
                            "real_time_conversion": report_data['real_time_conversion'],
                            "cpm": report_data['cpm'],
                            "impressions": report_data['impressions'],
                            "real_time_cost_per_conversion": report_data['real_time_cost_per_conversion'],
                            "ctr": report_data['ctr']
                        }
                        report_list.append(Reports(**report_dict))
                if len(report_list) > 0:
                    Reports.objects.bulk_create(report_list)
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
            metrics_list = ["stat_cost", "cpc", "cpm", "show_cnt", "click_cnt", "ctr", "time_attr_convert_cnt", "time_attr_conversion_cost", "time_attr_conversion_rate", "convert_cnt", "conversion_cost", "conversion_rate", "skan_convert_cnt", "skan_conversion_cost", "skan_conversion_rate"]
            metrics = json.dumps(metrics_list)
            data_level = 'AUCTION_ADVERTISER'
            end_date = today
            start_date = today
            report_type = 'BASIC'
            dimensions_list = ["advertiser_id"]
            dimensions = json.dumps(dimensions_list)

            # Args in JSON format
            my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
                metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
            reports = tiktok_get(my_args, path, access_token)
            response["data"] = reports['data']['list'][0]['metrics']
            response["success"] = True
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response



