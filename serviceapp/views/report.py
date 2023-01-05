import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers, Reports, CountryReports, MediaBuyerAdvertiser, VerticalAdvertiser
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.report_serializer import CountryReportSerializer, DailyReportSerializer
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper, UserPermissions, AdvertiserCalculateView, MediaAdvertiserCalculateView
from datetime import datetime, timedelta, date


class ReportView(APIView):

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_total_report(request):
        response = {}
        try:
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            query_filter = Q()
            query_filter &= Q(report_date__gte=start_date)
            query_filter &= Q(report_date__lte=end_date)
            if 'bc_id' in request.GET:
                bc_id = request.GET.get('bc_id')
                query_filter &= Q(advertiser_id__owner_bc_id=bc_id)
            reports = Reports.objects.filter(query_filter).aggregate(Sum('spend'), Sum('clicks'), Sum('conversion'),
                                                                     Sum('impressions'), Sum('revenue'))
            total_conversions = reports['conversion__sum'] if reports['conversion__sum'] else 0
            total_cost = reports['spend__sum'] if reports['spend__sum'] else 0.0
            total_clicks = reports['clicks__sum'] if reports['clicks__sum'] else 0
            total_impressions = reports['impressions__sum'] if reports['impressions__sum'] else 0
            total_revenue = reports['revenue__sum'] if reports['revenue__sum'] else 0.0
            report = {
                "conversions": total_conversions,
                "total_cost": round(total_cost, 2),
                "clicks": total_clicks,
                "impressions": total_impressions,
                "revenue": round(total_revenue, 2)
            }
            if report['clicks'] != 0:
                report['conversion_rate'] = round(report['conversions'] / (report['clicks'] / 100), 2)
                report['cpc'] = round((report['total_cost'] / report['clicks']), 2)
            else:
                report['conversion_rate'] = 0
                report['cpc'] = 0
            if report['impressions'] != 0:
                report['ctr'] = round((report['clicks'] / report['impressions']) * 100, 2)
                report['cpm'] = round((report['total_cost'] / report['impressions']) * 1000, 2)
            else:
                report['ctr'] = 0
                report['cpm'] = 0
            if report['conversions'] != 0:
                report['cpa'] = round((report['total_cost'] / report['conversions']), 2)
            else:
                report['cpa'] = 0
            report["profit"] = round(total_revenue - total_cost, 2)
            if total_cost > 0:
                report["roi"] = round((report["profit"] / total_cost) * 100, 2)
            else:
                report["roi"] = 0.0

            # get media buyer report
            media_buyer_report = ReportView.get_media_buyer_reports(request, start_date, end_date)

            # get Vertical report
            vertical_report = ReportView.get_vertical_reports(request, start_date, end_date)
            # get country report
            country_reports = CountryReports.objects.filter(query_filter).values('country', 'country_code').annotate(
                total_cost=Sum('spend'), ).exclude(country=None).order_by('-total_cost')[:5]
            serializer = CountryReportSerializer(country_reports, many=True)
            # get Activity report
            daily_reports = Reports.objects.filter(query_filter).values(
                'report_date').annotate(Count('advertiser_id', distinct=True), Sum('spend'), Sum('clicks'),
                                        Sum('conversion'), Sum('impressions'), Sum('revenue')).order_by('-report_date')
            report_serializer = DailyReportSerializer(daily_reports, many=True)
            response["data"] = {
                "total_repots": report,
                "country_repots": serializer.data,
                "activity_reports": report_serializer.data,
                "media_buyer_reports": media_buyer_report,
                "vertical_reports": vertical_report
            }
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
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            query_filter = Q()
            query_filter &= Q(report_date__gte=start_date)
            query_filter &= Q(report_date__lte=end_date)
            order_by = 'report_date'
            sort_by = True
            if 'sort_field' in request.GET:
                sort_field = request.GET.get('sort_field')
                order_by = sort_field
            if 'sort_by' in request.GET:
                sort_by = request.GET.get('sort_by')
                if sort_by == 'asc':
                    sort_by = False
                else:
                    sort_by = True
            if 'bc_id' in request.GET:
                bc_id = request.GET.get('bc_id')
                query_filter &= Q(advertiser_id__owner_bc_id=bc_id)
            daily_reports = Reports.objects.filter(query_filter).values('report_date').annotate(total_cost=Sum('spend'), clicks=Sum('clicks'),
                                        conversions=Sum('conversion'), impressions=Sum('impressions'), revenue=Sum('revenue')).order_by('-report_date').exclude(total_cost=0, impressions=0, revenue=0)
            for report in daily_reports:
                report['conversion_rate'] = MediaAdvertiserCalculateView.get_conversion_rate(request, report)
                report['total_cost'] = MediaAdvertiserCalculateView.get_total_cost(request, report)
                report['ctr'] = MediaAdvertiserCalculateView.get_ctr(request, report)
                report['cpm'] = MediaAdvertiserCalculateView.get_cpm(request, report)
                report['cpc'] = MediaAdvertiserCalculateView.get_cpc(request, report)
                report['cpa'] = MediaAdvertiserCalculateView.get_cpa(request, report)
                report['revenue'] = MediaAdvertiserCalculateView.get_revenue(request, report)
                report['profit'] = MediaAdvertiserCalculateView.get_profit(request, report)
                report['roi'] = MediaAdvertiserCalculateView.get_roi(request, report)
                report_list.append(report)
            new_sorted_list = sorted(report_list, key=lambda d: d[order_by], reverse=sort_by)
            daily_total_report = Reports.objects.filter(query_filter).aggregate(total_cost=Sum('spend'), clicks=Sum('clicks'),
                                        conversions=Sum('conversion'), impressions=Sum('impressions'), revenue=Sum('revenue'))
            daily_total_report['conversion_rate'] = MediaAdvertiserCalculateView.get_conversion_rate(request, daily_total_report)
            daily_total_report['total_cost'] = MediaAdvertiserCalculateView.get_total_cost(request, daily_total_report)
            daily_total_report['ctr'] = MediaAdvertiserCalculateView.get_ctr(request, daily_total_report)
            daily_total_report['cpm'] = MediaAdvertiserCalculateView.get_cpm(request, daily_total_report)
            daily_total_report['cpc'] = MediaAdvertiserCalculateView.get_cpc(request, daily_total_report)
            daily_total_report['cpa'] = MediaAdvertiserCalculateView.get_cpa(request, daily_total_report)
            daily_total_report['revenue'] = MediaAdvertiserCalculateView.get_revenue(request, daily_total_report)
            daily_total_report['profit'] = MediaAdvertiserCalculateView.get_profit(request, daily_total_report)
            daily_total_report['roi'] = MediaAdvertiserCalculateView.get_roi(request, daily_total_report)
            response["success"] = True
            response["data"] = new_sorted_list
            response["daily_total_report"] = daily_total_report
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_media_buyer_reports(request, start_date, end_date):
        response = {}
        try:
            # reports = Reports.objects.filter(query_filter).aggregate(Sum('spend'), Sum('clicks'), Sum('conversion'),
            #                                                          Sum('impressions'), Sum('revenue'))
            query_filter = Q()
            report_filter = Q()
            report_filter &= Q(report_date__gte=start_date)
            report_filter &= Q(report_date__lte=end_date)
            if 'query' in request.GET:
                name = request.GET.get('query')
                query_filter &= Q(media_buyer_id__name__icontains=name)
            advertiser = MediaBuyerAdvertiser.objects.values_list('advertiser_id', flat=True).filter(
                query_filter).distinct()
            report_filter &= Q(advertiser_id__in=advertiser)
            reports = Reports.objects.filter(report_filter).aggregate(
                total_cost=Sum('spend'), clicks=Sum('clicks'),
                conversions=Sum('conversion'),
                impressions=Sum('impressions'), revenue=Sum('revenue'))
            # query_filter &= Q(advertiser_id__reports__report_date__gte=start_date)
            # query_filter &= Q(advertiser_id__reports__report_date__lte=end_date)
            # reports = MediaBuyerAdvertiser.objects.filter(query_filter).aggregate(
            #     total_cost=Sum('advertiser_id__reports__spend'), clicks=Sum('advertiser_id__reports__clicks'),
            #     conversions=Sum('advertiser_id__reports__conversion'),
            #     impressions=Sum('advertiser_id__reports__impressions'), revenue=Sum('advertiser_id__reports__revenue'))
            total_conversions = reports['conversions'] if reports['conversions'] else 0
            total_cost = reports['total_cost'] if reports['total_cost'] else 0.0
            total_clicks = reports['clicks'] if reports['clicks'] else 0
            total_impressions = reports['impressions'] if reports['impressions'] else 0
            total_revenue = reports['revenue'] if reports['revenue'] else 0.0
            report = {
                "conversions": total_conversions,
                "total_cost": round(total_cost, 2),
                "clicks": total_clicks,
                "impressions": total_impressions,
                "revenue": round(total_revenue, 2)
            }
            if report['clicks'] != 0:
                report['conversion_rate'] = round(report['conversions'] / (report['clicks'] / 100), 2)
                report['cpc'] = round((report['total_cost'] / report['clicks']), 2)
            else:
                report['conversion_rate'] = 0
                report['cpc'] = 0
            if report['impressions'] != 0:
                report['ctr'] = round((report['clicks'] / report['impressions']) * 100, 2)
                report['cpm'] = round((report['total_cost'] / report['impressions']) * 1000, 2)
            else:
                report['ctr'] = 0
                report['cpm'] = 0
            if report['conversions'] != 0:
                report['cpa'] = round((report['total_cost'] / report['conversions']), 2)
            else:
                report['cpa'] = 0
            report["profit"] = round(total_revenue - total_cost, 2)
            if total_cost > 0:
                report["roi"] = round((report["profit"] / total_cost) * 100, 2)
            else:
                report["roi"] = 0.0
            print(report)
            response["success"] = True
            return report
        except Exception as e:
            LogHelper.efail(e)
            default_data = {
                "conversions": 0,
                "total_cost": 0.0,
                "clicks": 0,
                "impressions": 0,
                "revenue": 0.0,
                "conversion_rate": 0,
                "cpc": 0,
                "ctr": 0,
                "cpm": 0,
                "cpa": 0,
                "profit": 0.0,
                "roi": 0.0
            }
            return default_data

    def get_vertical_reports(request, start_date, end_date):
        response = {}
        try:
            query_filter = Q()
            report_filter = Q()
            report_filter &= Q(report_date__gte=start_date)
            report_filter &= Q(report_date__lte=end_date)
            if 'query' in request.GET:
                name = request.GET.get('query')
                query_filter &= Q(vertical_id__details__name__icontains=name)
            advertiser = VerticalAdvertiser.objects.values_list('advertiser_id', flat=True).filter(
                query_filter).distinct()
            report_filter &= Q(advertiser_id__in=advertiser)
            reports = Reports.objects.filter(report_filter).aggregate(
                total_cost=Sum('spend'), clicks=Sum('clicks'),
                conversions=Sum('conversion'),
                impressions=Sum('impressions'), revenue=Sum('revenue'))
            total_conversions = reports['conversions'] if reports['conversions'] else 0
            total_cost = reports['total_cost'] if reports['total_cost'] else 0.0
            total_clicks = reports['clicks'] if reports['clicks'] else 0
            total_impressions = reports['impressions'] if reports['impressions'] else 0
            total_revenue = reports['revenue'] if reports['revenue'] else 0.0
            report = {
                "conversions": total_conversions,
                "total_cost": round(total_cost, 2),
                "clicks": total_clicks,
                "impressions": total_impressions,
                "revenue": round(total_revenue, 2)
            }
            if report['clicks'] != 0:
                report['conversion_rate'] = round(report['conversions'] / (report['clicks'] / 100), 2)
                report['cpc'] = round((report['total_cost'] / report['clicks']), 2)
            else:
                report['conversion_rate'] = 0
                report['cpc'] = 0
            if report['impressions'] != 0:
                report['ctr'] = round((report['clicks'] / report['impressions']) * 100, 2)
                report['cpm'] = round((report['total_cost'] / report['impressions']) * 1000, 2)
            else:
                report['ctr'] = 0
                report['cpm'] = 0
            if report['conversions'] != 0:
                report['cpa'] = round((report['total_cost'] / report['conversions']), 2)
            else:
                report['cpa'] = 0
            report["profit"] = round(total_revenue - total_cost, 2)
            if total_cost > 0:
                report["roi"] = round((report["profit"] / total_cost) * 100, 2)
            else:
                report["roi"] = 0.0
            print(report)
            response["success"] = True
            return report
        except Exception as e:
            LogHelper.efail(e)
            default_data = {
                "conversions": 0,
                "total_cost": 0.0,
                "clicks": 0,
                "impressions": 0,
                "revenue": 0.0,
                "conversion_rate": 0,
                "cpc": 0,
                "ctr": 0,
                "cpm": 0,
                "cpa": 0,
                "profit": 0.0,
                "roi": 0.0
            }
            return default_data

    # @api_view(["get"])
    # @permission_classes([UserPermissions])
    # def get_activity_report(request):
    #     response = {}
    #     try:
    #         report_type = request.GET.get('type')
    #         today = datetime.now().date()
    #         week_1 = today - timedelta(days=6)
    #         week_2_end = week_1 - timedelta(days=1)
    #         week_2_start = week_2_end - timedelta(days=6)
    #         reports = []
    #         if report_type == 'weekly':
    #             week_1_reports = Reports.objects.filter(report_date__lte=today, report_date__gte=week_1, spend__gt=0).aggregate(Count('advertiser_id', distinct=True),Sum('spend'), Sum('clicks'),Sum('conversion'), Sum('impressions'))
    #             week_2_reports = Reports.objects.filter(report_date__lte=week_2_end, report_date__gte=week_2_start, spend__gt=0).aggregate(Count('advertiser_id', distinct=True),Sum('spend'), Sum('clicks'),Sum('conversion'), Sum('impressions'))
    #             week_1_report = {
    #                 "conversions": week_1_reports['conversion__sum'],
    #                 "cost": round(week_1_reports['spend__sum'], 2),
    #                 "clicks": week_1_reports['clicks__sum'],
    #                 "impressions": week_1_reports['impressions__sum'],
    #                 "products": week_1_reports['advertiser_id__count'],
    #                 "start_date": week_1,
    #                 "end_date": today
    #             }
    #             reports.append(week_1_report)
    #             week_2_report = {
    #                 "conversions": week_2_reports['conversion__sum'],
    #                 "cost": round(week_2_reports['spend__sum'], 2),
    #                 "clicks": week_2_reports['clicks__sum'],
    #                 "impressions": week_2_reports['impressions__sum'],
    #                 "products": week_2_reports['advertiser_id__count'],
    #                 "start_date": week_2_start,
    #                 "end_date": week_2_end
    #             }
    #             reports.append(week_2_report)
    #         else:
    #             daily_reports = Reports.objects.filter(report_date__lte=today, report_date__gte=week_1, spend__gt=0).values('report_date').annotate(Count('advertiser_id', distinct=True), Sum('spend'), Sum('clicks'),
    #                                                                            Sum('conversion'), Sum('impressions')).order_by('-report_date')
    #             for data in daily_reports:
    #                 daily_report = {
    #                     "conversions": data['conversion__sum'],
    #                     "cost": round(data['spend__sum'], 2),
    #                     "clicks": data['clicks__sum'],
    #                     "impressions": data['impressions__sum'],
    #                     "products": data['advertiser_id__count'],
    #                     "start_date": data['report_date']
    #                 }
    #                 reports.append(daily_report)
    #         response["success"] = True
    #         response["data"] = reports
    #         response["success"] = True
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)

    #
    # def get_report_by_advertiser(request, advertiser_id, access_token, today):
    #     response = {}
    #     try:
    #         # Args in JSON format
    #         path = "/report/integrated/get/"
    #         metrics_list = ["stat_cost", "cpc", "cpm", "show_cnt", "click_cnt", "ctr", "time_attr_convert_cnt", "time_attr_conversion_cost", "time_attr_conversion_rate", "convert_cnt", "conversion_cost", "conversion_rate", "skan_convert_cnt", "skan_conversion_cost", "skan_conversion_rate"]
    #         metrics = json.dumps(metrics_list)
    #         data_level = 'AUCTION_ADVERTISER'
    #         end_date = today
    #         start_date = today
    #         report_type = 'BASIC'
    #         dimensions_list = ["advertiser_id"]
    #         dimensions = json.dumps(dimensions_list)
    #
    #         # Args in JSON format
    #         my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
    #             metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
    #         reports = tiktok_get(my_args, path, access_token)
    #         response["data"] = reports['data']['list'][0]['metrics']
    #         response["success"] = True
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #     return response
