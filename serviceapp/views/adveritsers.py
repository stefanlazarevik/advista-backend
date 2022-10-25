import json
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers
from rest_framework.decorators import api_view
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper


class AdvertiserView(APIView):

    # def get(self, request):
    #     serializer = UserSerializer(request.user)
    #     return Response(data=serializer.data, status=status.HTTP_200_OK)

    @api_view(["get"])
    def get_daily_advertisers(request):
        response = {}
        try:
            advertiser_ids = []
            tiktok_info = TiktokInfo.objects.get(id=1)
            access_token = tiktok_info.access_token
            secret = tiktok_info.secret
            app_id = tiktok_info.app_id

            # Args in JSON format
            path = "/oauth2/advertiser/get/"
            my_args = "{\"access_token\": \"%s\", \"secret\": \"%s\", \"app_id\": \"%s\"}" % (access_token, secret, app_id)
            adverisers = tiktok_get(my_args, path, access_token)
            for advertiser in adverisers['data']['list']:
                advertiser_ids.append(advertiser['advertiser_id'])
            # print(advertiser_ids)
            print(len(advertiser_ids))
            existing_advertisers = Advertisers.objects.values_list('advertiser_id', flat=True).filter(advertiser_id__in=advertiser_ids)
            new_advertisers = list(set(advertiser_ids).difference(existing_advertisers))
            # print(new_advertisers)
            print(len(new_advertisers))
            if len(new_advertisers) > 0 :
                save_advertisers = AdvertiserView.save_new_advertisers(request, new_advertisers, access_token)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def save_new_advertisers(request, advertiser_ids, access_token):
        response = {}
        try:
            advertiser_list = []
            # Args in JSON format
            path = "/advertiser/info/"
            my_args = "{\"advertiser_ids\": %s}" % (json.dumps(advertiser_ids))
            advertisers = tiktok_get(my_args, path, access_token)
            for advertiser in advertisers['data']['list']:
                advertiser_dict = {
                    "contacter": advertiser['contacter'],
                    "balance": advertiser['balance'],
                    "rejection_reason": advertiser['rejection_reason'],
                    "language": advertiser['language'],
                    "license_province": advertiser['license_province'],
                    "role": advertiser['role'],
                    "timezone": advertiser['timezone'],
                    "create_time": advertiser['create_time'],
                    "address": advertiser['address'],
                    "company": advertiser['company'],
                    "advertiser_account_type": advertiser['advertiser_account_type'],
                    "license_url": advertiser['license_url'],
                    "license_no": advertiser['license_no'],
                    "description": advertiser['description'],
                    "owner_bc_id": advertiser['owner_bc_id'],
                    "brand": advertiser['brand'],
                    "country": advertiser['country'],
                    "industry": advertiser['industry'],
                    "promotion_center_province": advertiser['promotion_center_province'],
                    "license_city": advertiser['license_city'],
                    "promotion_center_city": advertiser['promotion_center_city'],
                    "status": advertiser['status'],
                    "cellphone_number": advertiser['cellphone_number'],
                    "email": advertiser['email'],
                    "advertiser_id": advertiser['advertiser_id'],
                    "display_timezone": advertiser['display_timezone'],
                    "telephone_number": advertiser['telephone_number'],
                    "currency": advertiser['currency'],
                    "promotion_area": advertiser['promotion_area'],
                    "name": advertiser['name']
                }
                advertiser_list.append(Advertisers(**advertiser_dict))
            Advertisers.objects.bulk_create(advertiser_list)
            response["success"] = True
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response



