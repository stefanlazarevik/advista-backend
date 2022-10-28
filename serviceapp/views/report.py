import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers, Reports, CountryReports
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.report_serializer import CountryReportSerializer
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper, UserPermissions
from datetime import datetime, timedelta, date


class ReportView(APIView):

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_total_report(request):
        response = {}
        try:
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            reports = Reports.objects.filter(report_date__gte=start_date, report_date__lte=end_date).aggregate(Sum('spend'), Sum('clicks'),Sum('conversion'), Sum('impressions'))
            report = {
                "conversions": reports['conversion__sum'],
                "cost": reports['spend__sum'],
                "clicks": reports['clicks__sum'],
                "impressions": reports['impressions__sum']
            }
            report['conversion_rate'] = round(report['conversions']/(report['clicks']/100), 2)
            report['ctr'] = round((report['clicks'] / report['impressions']) * 100, 2)
            report['cpm'] = round((report['cost'] / report['impressions']) * 1000, 2)
            report['cpc'] = round((report['cost'] / report['clicks']), 2)
            # get country report
            country_reports = CountryReports.objects.filter(report_date__gte=start_date,
                                                            report_date__lte=end_date).values('country', 'country_code').annotate(
                total_cost=Sum('spend'), ).exclude(country=None).order_by('-total_cost')[:5]
            serializer = CountryReportSerializer(country_reports, many=True)
            response["data"] = {
                "total_repots": report,
                "country_repots": serializer.data,
            }
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_activity_report(request):
        response = {}
        try:
            report_type = request.GET.get('type')
            today = datetime.now().date()
            week_1 = today - timedelta(days=6)
            week_2_end = week_1 - timedelta(days=1)
            week_2_start = week_2_end - timedelta(days=6)
            reports = []
            if report_type == 'weekly':
                week_1_reports = Reports.objects.filter(report_date__lte=today, report_date__gte=week_1, spend__gt=0).aggregate(Count('advertiser_id', distinct=True),Sum('spend'), Sum('clicks'),Sum('conversion'), Sum('impressions'))
                week_2_reports = Reports.objects.filter(report_date__lte=week_2_end, report_date__gte=week_2_start, spend__gt=0).aggregate(Count('advertiser_id', distinct=True),Sum('spend'), Sum('clicks'),Sum('conversion'), Sum('impressions'))
                week_1_report = {
                    "conversions": week_1_reports['conversion__sum'],
                    "cost": round(week_1_reports['spend__sum'], 2),
                    "clicks": week_1_reports['clicks__sum'],
                    "impressions": week_1_reports['impressions__sum'],
                    "products": week_1_reports['advertiser_id__count'],
                    "start_date": week_1,
                    "end_date": today
                }
                reports.append(week_1_report)
                week_2_report = {
                    "conversions": week_2_reports['conversion__sum'],
                    "cost": round(week_2_reports['spend__sum'], 2),
                    "clicks": week_2_reports['clicks__sum'],
                    "impressions": week_2_reports['impressions__sum'],
                    "products": week_2_reports['advertiser_id__count'],
                    "start_date": week_2_start,
                    "end_date": week_2_end
                }
                reports.append(week_2_report)
            else:
                daily_reports = Reports.objects.filter(report_date__lte=today, report_date__gte=week_1, spend__gt=0).values('report_date').annotate(Count('advertiser_id', distinct=True), Sum('spend'), Sum('clicks'),
                                                                               Sum('conversion'), Sum('impressions')).order_by('-report_date')
                for data in daily_reports:
                    daily_report = {
                        "conversions": data['conversion__sum'],
                        "cost": round(data['spend__sum'], 2),
                        "clicks": data['clicks__sum'],
                        "impressions": data['impressions__sum'],
                        "products": data['advertiser_id__count'],
                        "start_date": data['report_date']
                    }
                    reports.append(daily_report)
            response["success"] = True
            response["data"] = reports
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @api_view(["get"])
    def get_daily_report(request):
        response = {}
        try:
            report_list = []
            today = datetime.now().date()
            # today = request.GET.get('today')
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



