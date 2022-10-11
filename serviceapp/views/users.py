import hashlib
import random
import string
import pytz

from rest_framework.permissions import BasePermission
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from serviceapp.models import Users
from serviceapp.serializers.user_serializer import UserSerializer
from serviceapp.views.helper import LogHelper
from datetime import datetime, timedelta, date
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import login_required
from django.db import transaction


class UserProfilePermissions(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False


class UserUploadPermissions(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        elif request.method == 'POST':
            return True
        return False


class AdminPermissions(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return False


class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    create:
    Create a new user instance.
    """
    queryset = Users.objects.all()
    serializer_class = UserSerializer
    permission_classes = (UserUploadPermissions,)

    def create(self, request, *args, **kwargs):
        # try:
        with transaction.atomic():
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                obj = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     LogHelper.efail(e)
        #     return Response({'status': False, 'message': "Something went wrong."},
        #                     status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserInfo(APIView):
    permission_classes = (UserProfilePermissions, )

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)



