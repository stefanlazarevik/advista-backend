from rest_framework import serializers
from serviceapp.models import Partners


class PartnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Partners
        fields = ('id', 'name', 'partner_id')