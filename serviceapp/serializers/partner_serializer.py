from rest_framework import serializers
from serviceapp.models import MediaBuyer, Vertical


class PartnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = MediaBuyer
        fields = ('id', 'name', 'email', 'media_buyer_id')


class VerticalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vertical
        fields = ('id', 'details', 'vertical_id', 'created_time')