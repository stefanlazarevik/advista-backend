
from rest_framework.permissions import BasePermission
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Users
from serviceapp.serializers.user_serializer import UserSerializer
from django.db import transaction


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



