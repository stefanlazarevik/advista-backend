from datetime import date, timedelta, datetime

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from serviceapp.models import Users


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    phone = serializers.CharField(required=False)
    avatar = serializers.SerializerMethodField()
    avatar_thumb = serializers.SerializerMethodField()
    # uuid = serializers.CharField(read_only=True)

    class Meta:
        model = Users
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'user_mode', 'is_superuser', 'password', 'confirm_password', 'phone', 'avatar', 'avatar_thumb')

    def get_avatar(self, user):
        if user.avatar:
            avatar = user.avatar.url
            return avatar
        else:
            return None

    def get_avatar_thumb(self, user):
        if user.avatar_thumb:
            avatar_thumb = user.avatar_thumb.url
            return avatar_thumb
        else:
            return None

    def create(self, validated_data):
        user_data = validated_data
        # user_data['phone'] = re.sub("\D", "", user_data['phone_number'])
        if Users.objects.filter(email=user_data.get('email')).exists():
            raise serializers.ValidationError({"message": "Email already exist"})
        if Users.objects.filter(username=user_data.get('username')).exists():
            raise serializers.ValidationError({"message": "Username already exist"})
        password = user_data['password']
        confirm_password = user_data.pop('confirm_password', '')
        if len(password) < 8:
            raise serializers.ValidationError({"message": "Password should be minimum 8 characters."})
        if password != confirm_password:
            raise serializers.ValidationError({"message": "Passwords did not match"})
        user_data['password'] = make_password(password=password)
        user_data['is_active'] = False
        user_data['email_expired_at'] = datetime.now() + timedelta(minutes=5)
        user = Users.objects.create(**user_data)
        return user