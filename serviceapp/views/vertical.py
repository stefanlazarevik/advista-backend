import json

from django.db.models import Q, Sum
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Vertical, VerticalAdvertiser
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.partner_serializer import VerticalSerializer
from serviceapp.views.helper import LogHelper, UserPermissions, CustomPagination, MediaAdvertiserCalculateView


class VerticalView(APIView):

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_verticals(request):
        response = {}
        try:
            query_filter = Q()
            order_by = 'id'
            sort_by = False
            vertical_list = []
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
                query_filter &= Q(details__name__icontains=query)
            verticals = Vertical.objects.filter(query_filter).order_by('id')
            for vertical in verticals:
                vertical_data = VerticalSerializer(vertical).data
                report_filter = Q(vertical_id=vertical)
                report_filter &= Q(advertiser_id__reports__report_date__gte=start_date)
                report_filter &= Q(advertiser_id__reports__report_date__lte=end_date)
                vertical_advertiser = VerticalAdvertiser.objects.filter(report_filter).aggregate(
                    total_cost=Sum('advertiser_id__reports__spend'), clicks=Sum('advertiser_id__reports__clicks'),
                    conversions=Sum('advertiser_id__reports__conversion'),
                    impressions=Sum('advertiser_id__reports__impressions'),
                    revenue=Sum('advertiser_id__reports__revenue'))
                vertical_data['conversion_rate'] = MediaAdvertiserCalculateView.get_conversion_rate(request,
                                                                                                       vertical_advertiser)
                vertical_data['total_cost'] = MediaAdvertiserCalculateView.get_total_cost(request, vertical_advertiser)
                vertical_data['name'] = vertical_data['details']['name']
                vertical_data['ctr'] = MediaAdvertiserCalculateView.get_ctr(request, vertical_advertiser)
                vertical_data['cpm'] = MediaAdvertiserCalculateView.get_cpm(request, vertical_advertiser)
                vertical_data['cpc'] = MediaAdvertiserCalculateView.get_cpc(request, vertical_advertiser)
                vertical_data['cpa'] = MediaAdvertiserCalculateView.get_cpa(request, vertical_advertiser)
                vertical_data['revenue'] = MediaAdvertiserCalculateView.get_revenue(request, vertical_advertiser)
                vertical_data['profit'] = MediaAdvertiserCalculateView.get_profit(request, vertical_advertiser)
                vertical_data['roi'] = MediaAdvertiserCalculateView.get_roi(request, vertical_advertiser)
                vertical_list.append(vertical_data)
            new_sorted_list = sorted(vertical_list, key=lambda d: d[order_by], reverse=sort_by)
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(new_sorted_list, request)
            response["success"] = True
            response["data"] = result_page
            return paginator.get_paginated_response(data=response)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)




