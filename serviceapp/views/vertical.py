import json
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
            verticals = Vertical.objects.all().order_by('-id')
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




