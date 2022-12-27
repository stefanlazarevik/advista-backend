import json

from django.db.models import Q, Sum
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, MediaBuyer, MediaBuyerAdvertiser
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.partner_serializer import PartnerSerializer
from serviceapp.views.report import ReportView
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper, UserPermissions, CustomPagination, MediaAdvertiserCalculateView


class PartnerView(APIView):

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_partners(request):
        response = {}
        try:
            query_filter = Q()
            query_filter = Q(Q(bc__contains=['PixelMind']) | Q(bc__contains=['PixelMind USD']))
            order_by = 'id'
            sort_by = False
            media_buyer_list = []
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if 'sort_field' in request.GET:
                sort_field = request.GET.get('sort_field')
                order_by = sort_field
            if 'sort_by' in request.GET:
                sort_by = request.GET.get('sort_by')
                if sort_by == 'asc':
                    sort_by = False
                else:
                    sort_by = True
            if 'query' in request.GET:
                query = request.GET.get('query')
                query_filter &= Q(Q(name__icontains=query) | Q(email__icontains=query))
            partners = MediaBuyer.objects.filter(query_filter).order_by('id')
            for partner in partners:
                media_buyer_data = PartnerSerializer(partner).data
                report_filter = Q(media_buyer_id=partner)
                report_filter &= Q(advertiser_id__reports__report_date__gte=start_date)
                report_filter &= Q(advertiser_id__reports__report_date__lte=end_date)
                media_advertiser = MediaBuyerAdvertiser.objects.filter(report_filter).aggregate(
                total_cost=Sum('advertiser_id__reports__spend'), clicks=Sum('advertiser_id__reports__clicks'),
                conversions=Sum('advertiser_id__reports__conversion'), impressions=Sum('advertiser_id__reports__impressions'), revenue=Sum('advertiser_id__reports__revenue'))
                if (media_advertiser['total_cost'] and media_advertiser['total_cost'] > 0) or (
                        media_advertiser['impressions'] and media_advertiser['impressions'] > 0) or (
                        media_advertiser['revenue'] and media_advertiser['revenue'] > 0):
                    media_buyer_data['conversion_rate'] = MediaAdvertiserCalculateView.get_conversion_rate(request, media_advertiser)
                    media_buyer_data['total_cost'] = MediaAdvertiserCalculateView.get_total_cost(request, media_advertiser)
                    media_buyer_data['clicks'] = media_advertiser['clicks']
                    media_buyer_data['conversions'] = media_advertiser['conversions']
                    media_buyer_data['impressions'] = media_advertiser['impressions']
                    media_buyer_data['ctr'] = MediaAdvertiserCalculateView.get_ctr(request, media_advertiser)
                    media_buyer_data['cpm'] = MediaAdvertiserCalculateView.get_cpm(request, media_advertiser)
                    media_buyer_data['cpc'] = MediaAdvertiserCalculateView.get_cpc(request, media_advertiser)
                    media_buyer_data['cpa'] = MediaAdvertiserCalculateView.get_cpa(request, media_advertiser)
                    media_buyer_data['revenue'] = MediaAdvertiserCalculateView.get_revenue(request, media_advertiser)
                    media_buyer_data['profit'] = MediaAdvertiserCalculateView.get_profit(request, media_advertiser)
                    media_buyer_data['roi'] = MediaAdvertiserCalculateView.get_roi(request, media_advertiser)
                    media_buyer_list.append(media_buyer_data)
            new_sorted_list = sorted(media_buyer_list, key=lambda d: d[order_by], reverse=sort_by)
            # paginator = CustomPagination()
            # result_page = paginator.paginate_queryset(new_sorted_list, request)
            # get media buyer report
            media_buyer_report = ReportView.get_media_buyer_reports(request, start_date, end_date)
            response["results"] = {
                "success": True,
                "data": new_sorted_list,
                "media_buyer_report": media_buyer_report
            }
            return Response(response, status=status.HTTP_200_OK)
            # return paginator.get_paginated_response(data=response)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # @api_view(["get"])
    # def get_daily_partners(request):
    #     response = {}
    #     try:
    #         partner_list = []
    #         tiktok_info = TiktokInfo.objects.get(id=1)
    #         access_token = tiktok_info.access_token
    #         bc_id = tiktok_info.bc_id
    #
    #         # Args in JSON format
    #         path = "/bc/partner/get/"
    #         my_args = "{\"bc_id\": \"%s\"}" % bc_id
    #         partners = tiktok_get(my_args, path, access_token)
    #         for partner in partners['data']['list']:
    #             if not Partners.objects.filter(partner_id=partner['bc_id']).exists():
    #                 partner_dict = {
    #                     "name": partner['bc_name'],
    #                     "partner_id": partner['bc_id']
    #                 }
    #                 partner_list.append(Partners(**partner_dict))
    #         Partners.objects.bulk_create(partner_list)
    #         response["success"] = True
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)



