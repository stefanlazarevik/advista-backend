import json

from django.db.models import Sum, Q, F, Case, When, Value, FloatField, ExpressionWrapper
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.adveriser_serializer import AdvertiserSerializer, AdvertiserCSVSerializer
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper, CustomPagination, UserPermissions, AdvertiserCalculateView
from django.db.models.functions.comparison import NullIf


class AdvertiserView(APIView):
    # permission_classes = (UserPermissions,)

    @api_view(["get"])
    def hello(request):
        response = {}
        try:
            response["success"] = True
            response["data"] = "Hello"
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_advertisers(request):
        response = {}
        try:
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            advertiser_list = []
            query_filter = Q()
            query_filter &= Q(reports__report_date__gte=start_date)
            query_filter &= Q(reports__report_date__lte=end_date)
            order_by = 'id'
            sort_by = False
            if 'sort_field' in request.GET:
                sort_field = request.GET.get('sort_field')
                if sort_field == "status":
                    sort_field = "status_code"
                order_by = sort_field
            if 'sort_by' in request.GET:
                sort_by = request.GET.get('sort_by')
                if sort_by == 'asc':
                    sort_by = False
                else:
                    sort_by = True
            if 'query' in request.GET:
                name = request.GET.get('query')
                query_filter &= Q(name__icontains=name)
            if 'bc_id' in request.GET:
                bc_id = request.GET.get('bc_id')
                query_filter &= Q(owner_bc_id=bc_id)
            advertisers = Advertisers.objects.filter(query_filter).annotate(
                total_cost=Sum('reports__spend'), clicks=Sum('reports__clicks'),
                conversions=Sum('reports__conversion'), impressions=Sum('reports__impressions'), revenue=Sum('reports__revenue')).order_by("id").exclude(total_cost=0, impressions=0, revenue=0)
            for advertiser in advertisers:
                advertiser.status = AdvertiserCalculateView.get_status(request, advertiser)
                advertiser.conversion_rate = AdvertiserCalculateView.get_conversion_rate(request, advertiser)
                advertiser.total_cost = AdvertiserCalculateView.get_total_cost(request, advertiser)
                advertiser.ctr = AdvertiserCalculateView.get_ctr(request, advertiser)
                advertiser.cpm = AdvertiserCalculateView.get_cpm(request, advertiser)
                advertiser.cpc = AdvertiserCalculateView.get_cpc(request, advertiser)
                advertiser.cpa = AdvertiserCalculateView.get_cpa(request, advertiser)
                advertiser.revenue = AdvertiserCalculateView.get_revenue(request, advertiser)
                advertiser.profit = AdvertiserCalculateView.get_profit(request, advertiser)
                advertiser.roi = AdvertiserCalculateView.get_roi(request, advertiser)
                advertiser_list.append(AdvertiserSerializer(advertiser).data)
            new_sorted_list = sorted(advertiser_list, key=lambda d: d[order_by], reverse=sort_by)
            # paginator = CustomPagination()
            # result_page = paginator.paginate_queryset(new_sorted_list, request)
            response["results"] = {
                "success": True,
                "data": new_sorted_list
            }
            return Response(response, status=status.HTTP_200_OK)
            # return paginator.get_paginated_response(data=response)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @api_view(["get"])
    def generate_csv(request):
        response = {}
        try:
            start_date = "2022-09-29"
            end_date = "2022-10-28"
            advertisers = Advertisers.objects.filter(reports__report_date__gte=start_date,
                                                     reports__report_date__lte=end_date).annotate(
                total_cost=Sum('reports__spend'), clicks=Sum('reports__clicks'),
                conversions=Sum('reports__conversion'), impressions=Sum('reports__impressions')).order_by('id')
            serializer = AdvertiserCSVSerializer(advertisers, many=True)
            import csv
            headers = {
                'name': 'Name',
                'company': 'Company',
                'total_cost': 'Cost',
                'clicks': 'Clicks',
                'conversion_rate': 'CVR(%)',
                'conversions': 'Conversions',
                'cpm': 'CPM',
                'cpc': 'CPC',
                'ctr': 'CTR(%)',
                'cpa': 'CPA',
                'impressions': 'Impressions'
            }
            fieldnames = ['name', 'company', 'total_cost', 'clicks', 'conversion_rate', 'conversions', 'cpm', 'cpc', 'ctr', 'cpa', 'impressions']
            rows = serializer.data
            with open('reports.csv', 'w', encoding='UTF8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                # writer.writeheader()
                writer.writerow(headers)
                writer.writerows(rows)
            response["success"] = True
            response["data"] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # @api_view(["get"])
    # def generate_ad_csv(request):
    #     response = {}
    #     try:
    #         tiktok_info = TiktokInfo.objects.get(id=1)
    #         access_token = tiktok_info.access_token
    #         advertisers = Advertisers.objects.all()
    #         for advertiser in advertisers:
    #             daily_report = AdvertiserView.get_ad_report_by_advertiser(request, advertiser.advertiser_id, access_token)
    #             if 'data' in daily_report:
    #                 # daily_report['data']['advertiser_id'] = advertiser
    #                 # daily_report['data']['report_date'] = daily_report['report_date']
    #                 report_data = daily_report['data']
    #                 report_dict = {
    #                     "advertiser_id": advertiser,
    #                     "clicks": report_data['clicks'],
    #                     "conversion": report_data['conversion'],
    #                     "skan_conversion": report_data['skan_conversion'],
    #                     "cpc": report_data['cpc'],
    #                     "cost_per_conversion": report_data['cost_per_conversion'],
    #                     "conversion_rate": report_data['conversion_rate'],
    #                     "skan_cost_per_conversion": report_data['skan_cost_per_conversion'],
    #                     "spend": report_data['spend'],
    #                     "skan_conversion_rate": report_data['skan_conversion_rate'],
    #                     "real_time_conversion": report_data['real_time_conversion'],
    #                     "cpm": report_data['cpm'],
    #                     "impressions": report_data['impressions'],
    #                     "real_time_cost_per_conversion": report_data['real_time_cost_per_conversion'],
    #                     "ctr": report_data['ctr']
    #                 }
    #         serializer = AdvertiserCSVSerializer(advertisers, many=True)
    #         import csv
    #         headers = {
    #             'name': 'Name',
    #             'company': 'Company',
    #             'total_cost': 'Cost',
    #             'clicks': 'Clicks',
    #             'conversion_rate': 'CVR(%)',
    #             'conversions': 'Conversions',
    #             'cpm': 'CPM',
    #             'cpc': 'CPC',
    #             'ctr': 'CTR(%)',
    #             'cpa': 'CPA',
    #             'impressions': 'Impressions'
    #         }
    #         fieldnames = ['name', 'company', 'total_cost', 'clicks', 'conversion_rate', 'conversions', 'cpm', 'cpc',
    #                       'ctr', 'cpa', 'impressions']
    #         rows = serializer.data
    #         with open('reports.csv', 'w', encoding='UTF8', newline='') as f:
    #             writer = csv.DictWriter(f, fieldnames=fieldnames)
    #             # writer.writeheader()
    #             writer.writerow(headers)
    #             writer.writerows(rows)
    #         response["success"] = True
    #         response["data"] = serializer.data
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)
    #
    # def get_ad_report_by_advertiser(request, advertiser_id, access_token, today):
    #     response = {}
    #     try:
    #         # Args in JSON format
    #         path = "/report/integrated/get/"
    #         metrics_list = ["stat_cost", "cpc", "cpm", "show_cnt", "click_cnt", "ctr", "time_attr_convert_cnt", "time_attr_conversion_cost", "time_attr_conversion_rate", "convert_cnt", "conversion_cost", "conversion_rate", "skan_convert_cnt", "skan_conversion_cost", "skan_conversion_rate"]
    #         metrics = json.dumps(metrics_list)
    #         data_level = 'AUCTION_AD'
    #         start_date = "2022-09-29"
    #         end_date = "2022-10-28"
    #         report_type = 'BASIC'
    #         dimensions_list = ["ad_id"]
    #         dimensions = json.dumps(dimensions_list)
    #
    #         # Args in JSON format
    #         my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
    #             metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
    #         reports = tiktok_get(my_args, path, access_token)
    #         for ad in reports['data']['list']:
    #             ad_id = ad["dimensions"]["ad_id"]
    #
    #         response["data"] = reports['data']['list']
    #         response["success"] = True
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #     return response
    #
    # def get_ad_data(request, advertiser_id, access_token, ad_id):
    #     response = {}
    #     try:
    #         # Args in JSON format
    #         path = "/report/integrated/get/"
    #         metrics_list = ["stat_cost", "cpc", "cpm", "show_cnt", "click_cnt", "ctr", "time_attr_convert_cnt", "time_attr_conversion_cost", "time_attr_conversion_rate", "convert_cnt", "conversion_cost", "conversion_rate", "skan_convert_cnt", "skan_conversion_cost", "skan_conversion_rate"]
    #         metrics = json.dumps(metrics_list)
    #         data_level = 'AUCTION_AD'
    #         start_date = "2022-09-29"
    #         end_date = "2022-10-28"
    #         report_type = 'BASIC'
    #         dimensions_list = ["ad_id"]
    #         dimensions = json.dumps(dimensions_list)
    #
    #         # Args in JSON format
    #         my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
    #             metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
    #         reports = tiktok_get(my_args, path, access_token)
    #         for ad in reports['data']['list']:
    #             add_id = ad["dimensions"]["ad_id"]
    #         response["data"] = reports['data']['list']
    #         response["success"] = True
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #     return response

    # @api_view(["get"])
    # def get_daily_advertisers(request):
    #     response = {}
    #     try:
    #         advertiser_ids = []
    #         tiktok_info = TiktokInfo.objects.get(id=1)
    #         access_token = tiktok_info.access_token
    #         secret = tiktok_info.secret
    #         app_id = tiktok_info.app_id
    #
    #         # Args in JSON format
    #         path = "/oauth2/advertiser/get/"
    #         my_args = "{\"access_token\": \"%s\", \"secret\": \"%s\", \"app_id\": \"%s\"}" % (access_token, secret, app_id)
    #         adverisers = tiktok_get(my_args, path, access_token)
    #         for advertiser in adverisers['data']['list']:
    #             advertiser_ids.append(advertiser['advertiser_id'])
    #         # print(advertiser_ids)
    #         print(len(advertiser_ids))
    #         existing_advertisers = Advertisers.objects.values_list('advertiser_id', flat=True).filter(advertiser_id__in=advertiser_ids)
    #         new_advertisers = list(set(advertiser_ids).difference(existing_advertisers))
    #         # print(new_advertisers)
    #         print(len(new_advertisers))
    #         if len(new_advertisers) > 0 :
    #             save_advertisers = AdvertiserView.save_new_advertisers(request, new_advertisers, access_token)
    #         response["success"] = True
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)
    #
    # def save_new_advertisers(request, advertiser_ids, access_token):
    #     response = {}
    #     try:
    #         advertiser_list = []
    #         # Args in JSON format
    #         path = "/advertiser/info/"
    #         my_args = "{\"advertiser_ids\": %s}" % (json.dumps(advertiser_ids))
    #         advertisers = tiktok_get(my_args, path, access_token)
    #         for advertiser in advertisers['data']['list']:
    #             advertiser_dict = {
    #                 "contacter": advertiser['contacter'],
    #                 "balance": advertiser['balance'],
    #                 "rejection_reason": advertiser['rejection_reason'],
    #                 "language": advertiser['language'],
    #                 "license_province": advertiser['license_province'],
    #                 "role": advertiser['role'],
    #                 "timezone": advertiser['timezone'],
    #                 "create_time": advertiser['create_time'],
    #                 "address": advertiser['address'],
    #                 "company": advertiser['company'],
    #                 "advertiser_account_type": advertiser['advertiser_account_type'],
    #                 "license_url": advertiser['license_url'],
    #                 "license_no": advertiser['license_no'],
    #                 "description": advertiser['description'],
    #                 "owner_bc_id": advertiser['owner_bc_id'],
    #                 "brand": advertiser['brand'],
    #                 "country": advertiser['country'],
    #                 "industry": advertiser['industry'],
    #                 "promotion_center_province": advertiser['promotion_center_province'],
    #                 "license_city": advertiser['license_city'],
    #                 "promotion_center_city": advertiser['promotion_center_city'],
    #                 "status": advertiser['status'],
    #                 "cellphone_number": advertiser['cellphone_number'],
    #                 "email": advertiser['email'],
    #                 "advertiser_id": advertiser['advertiser_id'],
    #                 "display_timezone": advertiser['display_timezone'],
    #                 "telephone_number": advertiser['telephone_number'],
    #                 "currency": advertiser['currency'],
    #                 "promotion_area": advertiser['promotion_area'],
    #                 "name": advertiser['name']
    #             }
    #             advertiser_list.append(Advertisers(**advertiser_dict))
    #         Advertisers.objects.bulk_create(advertiser_list)
    #         response["success"] = True
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #     return response



