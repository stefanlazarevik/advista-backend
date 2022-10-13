import random
import string

from rest_framework.permissions import BasePermission
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Users
from serviceapp.serializers.user_serializer import UserSerializer
from django.db import transaction
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist

from serviceapp.views.common import CommonView
from serviceapp.views.helper import LogHelper
from datetime import datetime, timedelta, date
from django.conf import settings


class UserProfilePermissions(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False


class UserCreatePermissions(BasePermission):
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


class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    create:
    Create a new user instance.
    """
    serializer_class = UserSerializer

    permission_classes_by_action = {'create': [UserCreatePermissions], 'list': [AdminPermissions], 'update': [AdminPermissions]}

    def get_queryset(self):
        queryset = Users.objects.all().exclude(id=self.request.user.id).order_by('-id')
        return queryset

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                obj = serializer.save()
                verification_code = "".join(random.sample(string.digits, 5))
                obj.email_verification_token = verification_code
                obj.save()
                to = obj.email
                CommonView.send_verification_code(request, to, verification_code)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user_data = {}
        if "is_active" in request.data:
            user_data["is_active"] = request.data["is_active"]
        serializer = self.get_serializer(instance, data=user_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]


class UserInfo(APIView):
    permission_classes = (UserProfilePermissions, )

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @api_view(["post"])
    def email_verification(request):
        response = {}
        try:
            if request.user.is_authenticated:
                response['success'] = True
                response['message'] = "Already logged in"
                return Response(response, status=status.HTTP_200_OK)
            verification_code = request.data["code"]
            uuid = request.data["uuid"]
            user = Users.objects.get(email_verification_token=verification_code, uuid=uuid)
            if user.email_expired_at > date.today():
                user.is_verified = True
                user.save()
                response['success'] = True
                response['message'] = "Email verified"
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['success'] = False
                response['message'] = "Email authentication expired"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            response['success'] = False
            response['message'] = "Invaild Otp code"
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            LogHelper.efail(e)
            response['success'] = False
            response['message'] = "Something went wrong. Please try again"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @api_view(["post"])
    def resend_verification_code(request):
        response = {}
        try:
            if request.user.is_authenticated:
                response['success'] = True
                response['message'] = "Already logged in"
                return Response(response, status=status.HTTP_200_OK)
            uuid = request.data["uuid"]
            user = Users.objects.get(uuid=uuid)
            verification_code = "".join(random.sample(string.digits, 5))
            user.email_verification_token = verification_code
            user.email_expired_at = datetime.now() + timedelta(minutes=5)
            user.save()
            response['success'] = True
            response['message'] = "A new Verification has been sent"
            return Response(response, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            response['success'] = False
            response['message'] = "Invaild Otp code"
            return Response(response, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            LogHelper.efail(e)
            response['success'] = False
            response['message'] = "Something went wrong. Please try again"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)



