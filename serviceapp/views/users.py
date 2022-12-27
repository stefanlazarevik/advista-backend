import random
import string

from django.db.models import Q
from rest_framework.permissions import BasePermission
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Users, TiktokInfo
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
        if request.user.is_superuser or request.user.user_mode == "2":
            return True
        return False


class UserViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    create:
    Create a new user instance.
    """
    serializer_class = UserSerializer

    permission_classes_by_action = {'create': [UserCreatePermissions], 'list': [AdminPermissions], 'update': [AdminPermissions], 'retrive': [AdminPermissions]}

    def get_queryset(self):
        # queryset = Users.objects.filter(is_verified=True).exclude(id=self.request.user.id).order_by('-id')
        queryset = Users.objects.all().exclude(id=self.request.user.id).order_by('-id')
        return queryset

    def list(self, request, *args, **kwargs):
        response = {}
        try:
            query_filter = Q()
            if 'query' in request.GET:
                name = request.GET.get('query')
                query_filter &= Q(Q(username__icontains=name) | Q(first_name__icontains=name) | Q(last_name__icontains=name) | Q(email__icontains=name))
            # queryset = self.filter_queryset(self.get_queryset())
            queryset = Users.objects.filter(query_filter).exclude(id=self.request.user.id).order_by('-id')
            # page = self.paginate_queryset(queryset)
            # if page is not None:
            #     serializer = self.get_serializer(page, many=True)
            #     return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            response["results"] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            user_info = request.data
            serializer = UserSerializer(data=user_info)
            if serializer.is_valid():
                obj = serializer.save()
                response_data = serializer.data
                updated_data = {}
                if request.user.is_authenticated:
                    updated_data['created_by_id'] = request.user.id
                if 'avatar' in request.FILES:
                    avatar = request.FILES['avatar']
                    avatar_info = CommonView.handle_uploaded_file(avatar, obj)
                    if 'path' in avatar_info:
                        updated_data['avatar'] = avatar_info['path']
                        updated_data['avatar_thumb'] = avatar_info['thumb_path']
                if len(updated_data) != 0:
                    Users.objects.filter(id=obj.id).update(**updated_data)
                    user = Users.objects.get(id=obj.id)
                    user_serializer = UserSerializer(user)
                    response_data = user_serializer.data
                    response_data['created_by_id'] = user.created_by_id
                # verification_code = "".join(random.sample(string.digits, 5))
                # obj.email_verification_token = verification_code
                # obj.save()
                # to = obj.email
                # CommonView.send_verification_code(request, to, verification_code)
                return Response(response_data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # user_data = {}
        # if "is_active" in request.data:
        #     user_data["is_active"] = request.data["is_active"]
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_data = serializer.data
        updated_data = {
            "updated_by_id": request.user.id
        }
        if 'avatar' in request.FILES:
            avatar = request.FILES['avatar']
            avatar_info = CommonView.handle_uploaded_file(avatar, instance)
            if 'path' in avatar_info:
                updated_data['avatar'] = avatar_info['path']
                updated_data['avatar_thumb'] = avatar_info['thumb_path']
        if len(updated_data) != 0:
            Users.objects.filter(id=instance.id).update(**updated_data)
            user = Users.objects.get(id=instance.id)
            user_serializer = UserSerializer(user)
            response_data = user_serializer.data
            response_data['created_by_id'] = user.created_by_id
            response_data['updated_by_id'] = user.updated_by_id

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(response_data)

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
        currency = TiktokInfo.objects.get(id=1).bc_info['currency']
        data = serializer.data
        data['currency'] = currency
        return Response(data=data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs ):
        try:
            user_data = {}
            if "first_name" in request.data:
                user_data["first_name"] = request.data["first_name"]
            if "last_name" in request.data:
                user_data["last_name"] = request.data["last_name"]
            if "phone" in request.data:
                user_data["phone"] = request.data["phone"]
            Users.objects.filter(id=request.user.id).update(**user_data)
            user = Users.objects.get(id=request.user.id)
            serializer = UserSerializer(user)
            response_data = serializer.data
            if 'avatar' in request.FILES:
                updated_data = {}
                avatar = request.FILES['avatar']
                avatar_info = CommonView.handle_uploaded_file(avatar, user)
                if 'path' in avatar_info:
                    updated_data['avatar'] = avatar_info['path']
                    updated_data['avatar_thumb'] = avatar_info['thumb_path']
                    Users.objects.filter(id=user.id).update(**updated_data)
                    user = Users.objects.get(id=user.id)
                    user_serializer = UserSerializer(user)
                    response_data = user_serializer.data
            # new_serializer_data = dict(serializer.data)
            # new_serializer_data['avatar'] = CommonView.get_file_path(new_serializer_data['avatar'])
            # new_serializer_data['avatar_thumb'] = CommonView.get_file_path(new_serializer_data['avatar_thumb'])
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response = {
                "message": "Something went wrong. please try again"
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @api_view(["post"])
    # def email_verification(request):
    #     response = {}
    #     try:
    #         if request.user.is_authenticated:
    #             response['success'] = True
    #             response['message'] = "Already logged in"
    #             return Response(response, status=status.HTTP_200_OK)
    #         verification_code = request.data["code"]
    #         uuid = request.data["uuid"]
    #         user = Users.objects.get(email_verification_token=verification_code, uuid=uuid)
    #         if user.email_expired_at > date.today():
    #             user.is_verified = True
    #             user.save()
    #             response['success'] = True
    #             response['message'] = "Email verified"
    #             return Response(response, status=status.HTTP_200_OK)
    #         else:
    #             response['success'] = False
    #             response['message'] = "Email authentication expired"
    #             return Response(response, status=status.HTTP_400_BAD_REQUEST)
    #     except ObjectDoesNotExist:
    #         response['success'] = False
    #         response['message'] = "Invaild Otp code"
    #         return Response(response, status=status.HTTP_404_NOT_FOUND)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response['success'] = False
    #         response['message'] = "Something went wrong. Please try again"
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)
    #
    # @api_view(["post"])
    # def resend_verification_code(request):
    #     response = {}
    #     try:
    #         if request.user.is_authenticated:
    #             response['success'] = True
    #             response['message'] = "Already logged in"
    #             return Response(response, status=status.HTTP_200_OK)
    #         uuid = request.data["uuid"]
    #         user = Users.objects.get(uuid=uuid)
    #         verification_code = "".join(random.sample(string.digits, 5))
    #         user.email_verification_token = verification_code
    #         user.email_expired_at = datetime.now() + timedelta(minutes=5)
    #         user.save()
    #         response['success'] = True
    #         response['message'] = "A new Verification has been sent"
    #         return Response(response, status=status.HTTP_200_OK)
    #     except ObjectDoesNotExist:
    #         response['success'] = False
    #         response['message'] = "Invaild Otp code"
    #         return Response(response, status=status.HTTP_404_NOT_FOUND)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response['success'] = False
    #         response['message'] = "Something went wrong. Please try again"
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)



