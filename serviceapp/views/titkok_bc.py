import json

from django.db.models import Q, Sum
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokBC
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.bc_serializer import BCSerializer
from serviceapp.serializers.partner_serializer import VerticalSerializer
from serviceapp.views.helper import LogHelper, UserPermissions, CustomPagination, MediaAdvertiserCalculateView


class BCView(APIView):

    @api_view(["get"])
    @permission_classes([UserPermissions])
    def get_bc(request):
        response = {}
        try:
            bc = TiktokBC.objects.all()
            serializer = BCSerializer(bc, many=True)
            response["success"] = True
            response["data"] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)




