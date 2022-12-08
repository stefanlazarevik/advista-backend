import json

from django.db.models import Q
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Vertical
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.partner_serializer import VerticalSerializer
from serviceapp.views.helper import LogHelper, UserPermissions, CustomPagination


class VerticalView(APIView):

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_verticals(request):
        response = {}
        try:
            query_filter = Q()
            order_by_field = 'id'
            sort_by = False
            if 'sort_field' in request.GET:
                sort_field = request.GET.get('sort_field')
                order_by_field = sort_field
            if 'sort_by' in request.GET:
                sort_by = request.GET.get('sort_by')
                if sort_by == 'asc':
                    sort_by = True
                else:
                    sort_by = False
            if 'query' in request.GET:
                query = request.GET.get('query')
                query_filter &= Q(details__name__icontains=query)
            if sort_by:
                order_by = 'details__' + order_by_field
            else:
                order_by = '-' + 'details__' + order_by_field
            verticals = Vertical.objects.filter(query_filter).order_by(order_by)
            paginator = CustomPagination()
            result_page = paginator.paginate_queryset(verticals, request)
            serializer = VerticalSerializer(result_page, many=True)
            response["success"] = True
            response["data"] = serializer.data
            return paginator.get_paginated_response(data=response)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)




