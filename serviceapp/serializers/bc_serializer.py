from rest_framework import serializers
from serviceapp.models import TiktokBC


class BCSerializer(serializers.ModelSerializer):

    class Meta:
        model = TiktokBC
        fields = ('id', 'bc_id', 'bc_info', 'user_role', 'ext_user_role')