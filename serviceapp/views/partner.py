import json
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Partners
from rest_framework.decorators import api_view
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper


class PartnerView(APIView):

    # def get(self, request):
    #     serializer = UserSerializer(request.user)
    #     return Response(data=serializer.data, status=status.HTTP_200_OK)

    @api_view(["get"])
    def get_daily_partners(request):
        response = {}
        try:
            partner_list = []
            tiktok_info = TiktokInfo.objects.get(id=1)
            access_token = tiktok_info.access_token
            bc_id = tiktok_info.bc_id

            # Args in JSON format
            path = "/bc/partner/get/"
            my_args = "{\"bc_id\": \"%s\"}" % bc_id
            partners = tiktok_get(my_args, path, access_token)
            for partner in partners['data']['list']:
                if not Partners.objects.filter(partner_id=partner['bc_id']).exists():
                    partner_dict = {
                        "name": partner['bc_name'],
                        "partner_id": partner['bc_id']
                    }
                    partner_list.append(Partners(**partner_dict))
            Partners.objects.bulk_create(partner_list)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)



