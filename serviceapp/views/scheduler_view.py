import json
import math
import time

from pytz import timezone
import pycountry
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import TiktokInfo, Advertisers, Reports, CountryReports, Partners, Campaigns, CampaignReports
from rest_framework.decorators import api_view, permission_classes

from serviceapp.serializers.report_serializer import CountryReportSerializer, DailyReportSerializer
from serviceapp.views.tiktok_api import tiktok_get
from serviceapp.views.helper import LogHelper, UserPermissions
from datetime import datetime, timedelta, date
from .airtable_api import AirtableView
from serviceapp.views.tonic_api import get_access_token, get_tonic_daily_report


class SchedulerView(APIView):

    @api_view(["get"])
    def get_scheduler_data(request):
        response = {}
        try:
            # advertisers = SchedulerView.get_daily_advertisers(request)
            # reports = SchedulerView.get_daily_report(request)
            # country_reports = SchedulerView.get_daily_country_report(request)
            # partners = SchedulerView.get_daily_partners(request)
            # campaigns = SchedulerView.get_daily_campaigns(request)
            airtable = SchedulerView.get_airtable_data(request)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

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
            my_args = "{\"access_token\": \"%s\", \"secret\": \"%s\", \"app_id\": \"%s\"}" % (
                access_token, secret, app_id)
            advertisers = tiktok_get(my_args, path, access_token)
            for advertiser in advertisers['data']['list']:
                advertiser_ids.append(advertiser['advertiser_id'])
            # print(advertiser_ids)
            print(len(advertiser_ids))
            existing_advertisers = Advertisers.objects.values_list('advertiser_id', flat=True).filter(
                advertiser_id__in=advertiser_ids)
            new_advertisers = list(set(advertiser_ids).difference(existing_advertisers))
            # print(new_advertisers)
            print(len(new_advertisers))
            if len(new_advertisers) > 0:
                save_advertisers = SchedulerView.save_new_advertisers(request, new_advertisers, access_token)
            update_advertisers = SchedulerView.update_existing_advertisers(request, list(existing_advertisers),
                                                                           access_token)
            response["success"] = True
            print('-----------------------end-get_adverser-----------------')
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
                if advertiser['status'] == "STATUS_ENABLE":
                    advertiser_dict['status_code'] = "active"
                elif advertiser['status'] == "STATUS_DISABLE":
                    advertiser_dict['status_code'] = "disabled"
                elif advertiser['status'] == "STATUS_PENDING_VERIFIED":
                    advertiser_dict['status_code'] = "verification"
                elif advertiser['status'] == "STATUS_LIMIT":
                    advertiser_dict['status_code'] = "limit"
                elif advertiser['status'] in ["STATUS_CONFIRM_FAIL", "STATUS_CONFIRM_FAIL_END",
                                              "STATUS_CONFIRM_MODIFY_FAIL"]:
                    advertiser_dict['status_code'] = "failed"
                else:
                    advertiser_dict['status_code'] = "review"
                advertiser_list.append(Advertisers(**advertiser_dict))
            Advertisers.objects.bulk_create(advertiser_list)
            response["success"] = True
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response

    def update_existing_advertisers(request, advertiser_ids, access_token):
        response = {}
        try:
            offset = 0
            limit = 100
            total_advertiser_ids = len(advertiser_ids)
            total_page = math.ceil(total_advertiser_ids / limit)
            advertiser_list = []
            advertiser_data = {}
            # Args in JSON format
            path = "/advertiser/info/"
            while total_page:
                my_args = "{\"advertiser_ids\": %s}" % (json.dumps(advertiser_ids[offset:limit]))
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
                    if advertiser['status'] == "STATUS_ENABLE":
                        advertiser_dict['status_code'] = "active"
                    elif advertiser['status'] == "STATUS_DISABLE":
                        advertiser_dict['status_code'] = "disabled"
                    elif advertiser['status'] == "STATUS_PENDING_VERIFIED":
                        advertiser_dict['status_code'] = "verification"
                    elif advertiser['status'] == "STATUS_LIMIT":
                        advertiser_dict['status_code'] = "limit"
                    elif advertiser['status'] in ["STATUS_CONFIRM_FAIL", "STATUS_CONFIRM_FAIL_END",
                                                  "STATUS_CONFIRM_MODIFY_FAIL"]:
                        advertiser_dict['status_code'] = "failed"
                    else:
                        advertiser_dict['status_code'] = "review"
                    advertiser_data[advertiser['advertiser_id']] = advertiser_dict
                offset = limit
                limit = offset + limit
                total_page = total_page - 1
            existing_advertisers = Advertisers.objects.filter(advertiser_id__in=advertiser_ids)
            for advertiser in existing_advertisers:
                for key in advertiser_data[advertiser.advertiser_id]:
                    setattr(advertiser, key, advertiser_data[advertiser.advertiser_id][key])
                advertiser_list.append(advertiser)
            Advertisers.objects.bulk_update(advertiser_list,
                                            ["contacter", "balance", "rejection_reason", "language",
                                             "license_province", "role", "timezone", "create_time",
                                             "address", "company", "advertiser_account_type", "license_url",
                                             "license_no", "owner_bc_id", "brand", "country",
                                             "industry", "promotion_center_province", "status", "cellphone_number",
                                             "email", "advertiser_id", "display_timezone", "telephone_number",
                                             "currency", "promotion_area", "name", "status_code"])
            response["success"] = True

        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)

        return response

    def get_daily_report(request):
        response = {}
        try:
            report_list = []
            # today = datetime.now().date()
            # today = request.GET.get('today')
            # today = datetime.strptime(today, "%Y-%m-%d").date()
            # prev_day = today + timedelta(days=-1)
            # if not Reports.objects.filter(report_date=today).exists():
            tiktok_info = TiktokInfo.objects.get(id=1)
            access_token = tiktok_info.access_token
            advertisers = Advertisers.objects.all()
            for advertiser in advertisers:
                # x = range(3)
                # for n in x:
                # timezone_date = prev_day + timedelta(days=n)
                # timezone_date = request.GET.get('today')
                timezone_date = SchedulerView.convert_datetime_timezone(advertiser.display_timezone)
                daily_report = SchedulerView.get_report_by_advertiser(request, advertiser.advertiser_id, access_token,
                                                                      timezone_date)
                if 'data' in daily_report:
                    # daily_report['data']['advertiser_id'] = advertiser
                    # daily_report['data']['report_date'] = daily_report['report_date']
                    report_data = daily_report['data']
                    report_dict = {
                        "advertiser_id": advertiser,
                        "report_date": timezone_date,
                        "clicks": report_data['clicks'],
                        "conversion": report_data['conversion'],
                        "skan_conversion": report_data['skan_conversion'],
                        "cpc": report_data['cpc'],
                        "cost_per_conversion": report_data['cost_per_conversion'],
                        "conversion_rate": report_data['conversion_rate'],
                        "skan_cost_per_conversion": report_data['skan_cost_per_conversion'],
                        "spend": report_data['spend'],
                        "skan_conversion_rate": report_data['skan_conversion_rate'],
                        "real_time_conversion": report_data['real_time_conversion'],
                        "cpm": report_data['cpm'],
                        "impressions": report_data['impressions'],
                        "real_time_cost_per_conversion": report_data['real_time_cost_per_conversion'],
                        "ctr": report_data['ctr']
                    }
                    report, created = Reports.objects.update_or_create(
                        advertiser_id=advertiser, report_date=timezone_date, defaults=report_dict
                    )
                    # report_list.append(Reports(**report_dict))
            # if len(report_list) > 0:
            #     Reports.objects.bulk_create(report_list)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_report_by_advertiser(request, advertiser_id, access_token, today):
        response = {}
        try:
            # Args in JSON format
            path = "/report/integrated/get/"
            metrics_list = ["stat_cost", "cpc", "cpm", "show_cnt", "click_cnt", "ctr", "time_attr_convert_cnt",
                            "time_attr_conversion_cost", "time_attr_conversion_rate", "convert_cnt", "conversion_cost",
                            "conversion_rate", "skan_convert_cnt", "skan_conversion_cost", "skan_conversion_rate"]
            metrics = json.dumps(metrics_list)
            data_level = 'AUCTION_ADVERTISER'
            end_date = today
            start_date = today
            report_type = 'BASIC'
            dimensions_list = ["advertiser_id"]
            dimensions = json.dumps(dimensions_list)

            # Args in JSON format
            my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
                metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
            reports = tiktok_get(my_args, path, access_token)
            response["data"] = reports['data']['list'][0]['metrics']
            response["success"] = True
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response

    def get_daily_country_report(request):
        response = {}
        try:
            report_list = []
            # today = datetime.now().date()
            # today = request.GET.get('today')
            # today = datetime.strptime(today, "%Y-%m-%d").date()
            # prev_day = today + timedelta(days=-1)
            # if not CountryReports.objects.filter(report_date=today).exists():
            tiktok_info = TiktokInfo.objects.get(id=1)
            access_token = tiktok_info.access_token
            advertisers = Advertisers.objects.all()
            for advertiser in advertisers:
                # x = range(3)
                # for n in x:
                # timezone_date = prev_day + timedelta(days=n)
                # timezone_date = request.GET.get('today')
                timezone_date = SchedulerView.convert_datetime_timezone(advertiser.display_timezone)
                daily_report = SchedulerView.get_country_report_by_advertiser(request, advertiser.advertiser_id,
                                                                              access_token, timezone_date)
                if 'data' in daily_report:
                    report_data = daily_report['data']
                    for report in report_data:
                        data = report['metrics']
                        country_code = report['dimensions']['country_code']
                        data['country_code'] = None
                        data['country'] = None
                        if country_code != 'None':
                            data['country_code'] = country_code
                            country = pycountry.countries.get(alpha_2=country_code)
                            data['country'] = country.name
                            report_dict = {
                                "advertiser_id": advertiser,
                                "report_date": timezone_date,
                                "cost_per_conversion": data['cost_per_conversion'],
                                "ctr": data['ctr'],
                                "cpc": data['cpc'],
                                "spend": data['spend'],
                                "impressions": data['impressions'],
                                "clicks": data['clicks'],
                                "cpm": data['cpm'],
                                "conversion": data['conversion'],
                                "conversion_rate": data['conversion_rate'],
                                "reach": data['reach'],
                                "country": data['country'],
                                "country_code": data['country_code']
                            }
                            try:
                                report, created = CountryReports.objects.update_or_create(
                                    advertiser_id=advertiser, report_date=timezone_date, country_code=country_code,
                                    defaults=report_dict
                                )
                            except Exception as e:
                                print(LogHelper.efail(e))
                                country = CountryReports.objects.filter(advertiser_id=advertiser,
                                                                        report_date=timezone_date,
                                                                        country_code=country_code)
                                if country.exits():
                                    country = country[0]
                                    CountryReports.objects.filter(id=country.id).update(**report_dict)
                            # report_list.append(CountryReports(**report_dict))
            # if len(report_list) > 0:
            #     CountryReports.objects.bulk_create(report_list)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_country_report_by_advertiser(request, advertiser_id, access_token, today):
        response = {}
        try:
            # Args in JSON format
            path = "/report/integrated/get/"
            metrics_list = ["spend", "impressions", "cpc", "cpm", "ctr", "reach", "clicks", "stat_cost", "show_cnt",
                            "click_cnt", "time_attr_convert_cnt", "time_attr_conversion_cost",
                            "time_attr_conversion_rate"]
            metrics = json.dumps(metrics_list)
            data_level = 'AUCTION_ADVERTISER'
            end_date = today
            start_date = today
            report_type = 'BASIC'
            dimensions_list = ["country_code"]
            dimensions = json.dumps(dimensions_list)

            # Args in JSON format
            my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"report_type\": \"%s\", \"dimensions\": %s}" % (
                metrics, data_level, end_date, start_date, advertiser_id, report_type, dimensions)
            reports = tiktok_get(my_args, path, access_token)
            if 'list' in reports['data'] and len(reports['data']['list']) > 0:
                response["data"] = reports['data']['list']
            response["success"] = True
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response

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
                # if not Partners.objects.filter(partner_id=partner['bc_id']).exists():
                partner_dict = {
                    "name": partner['bc_name'],
                    "partner_id": partner['bc_id']
                }
                # partner_list.append(Partners(**partner_dict))
                partner, created = Partners.objects.update_or_create(
                    partner_id=partner['bc_id'], defaults=partner_dict
                )
            # Partners.objects.bulk_create(partner_list)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_daily_campaigns(request):
        response = {}
        update_campaign_data = []
        create_campaign_data = []
        try:
            tiktok_info = TiktokInfo.objects.get(id=1)
            access_token = tiktok_info.access_token
            advertisers = Advertisers.objects.all()
            for advertiser in advertisers:
                campaigns = SchedulerView.get_campaign_by_advertiser(request, advertiser.advertiser_id,
                                                                     access_token)
                if 'data' in campaigns:
                    campaigns_ids = [campaign["campaign_id"] for campaign in campaigns['data']]
                    existing_campaign = Campaigns.objects.values_list('campaign_id', flat=True).filter(
                        campaign_id__in=campaigns_ids)
                    new_campaign = list(set(campaigns_ids).difference(existing_campaign))
                    for campaign in campaigns['data']:
                        if campaign['campaign_id'] not in new_campaign:
                            update_campaign_data.append(Campaigns(
                                pk=campaign["campaign_id"],
                                advertiser_id=advertiser,
                                is_new_structure=campaign["is_new_structure"],
                                modify_time=campaign["modify_time"] if 'modify_time' in campaign else None,
                                campaign_id=campaign["campaign_id"],
                                operation_status=campaign[
                                    "operation_status"] if 'operation_status' in campaign else None,
                                objective=campaign["objective"] if 'objective' in campaign else None,
                                is_smart_performance_campaign=campaign[
                                    "is_smart_performance_campaign"] if 'is_smart_performance_campaign' in campaign else None,
                                budget_mode=campaign["budget_mode"] if 'budget_mode' in campaign else None,
                                deep_bid_type=campaign["deep_bid_type"] if 'deep_bid_type' in campaign else None,
                                budget=campaign["budget"] if 'budget' in campaign else None,
                                campaign_name=campaign["campaign_name"] if 'campaign_name' in campaign else None,
                                campaign_type=campaign["campaign_type"] if 'campaign_type' in campaign else None,
                                create_time=campaign["create_time"],
                                rf_campaign_type=campaign[
                                    "rf_campaign_type"] if 'rf_campaign_type' in campaign else None,
                                objective_type=campaign["objective_type"] if 'objective_type' in campaign else None,
                                secondary_status=campaign[
                                    "secondary_status"] if 'secondary_status' in campaign else None,
                                roas_bid=campaign["roas_bid"] if 'roas_bid' in campaign else None,
                                app_promotion_type=campaign[
                                    "app_promotion_type"] if 'app_promotion_type' in campaign else None
                            ))
                        else:
                            create_campaign_data.append(Campaigns(
                                advertiser_id=advertiser,
                                is_new_structure=campaign["is_new_structure"],
                                modify_time=campaign["modify_time"] if 'modify_time' in campaign else None,
                                campaign_id=campaign["campaign_id"],
                                operation_status=campaign[
                                    "operation_status"] if 'operation_status' in campaign else None,
                                objective=campaign["objective"] if 'objective' in campaign else None,
                                is_smart_performance_campaign=campaign[
                                    "is_smart_performance_campaign"] if 'is_smart_performance_campaign' in campaign else None,
                                budget_mode=campaign["budget_mode"] if 'budget_mode' in campaign else None,
                                deep_bid_type=campaign["deep_bid_type"] if 'deep_bid_type' in campaign else None,
                                budget=campaign["budget"] if 'budget' in campaign else None,
                                campaign_name=campaign["campaign_name"] if 'campaign_name' in campaign else None,
                                campaign_type=campaign["campaign_type"] if 'campaign_type' in campaign else None,
                                create_time=campaign["create_time"],
                                rf_campaign_type=campaign[
                                    "rf_campaign_type"] if 'rf_campaign_type' in campaign else None,
                                objective_type=campaign["objective_type"] if 'objective_type' in campaign else None,
                                secondary_status=campaign[
                                    "secondary_status"] if 'secondary_status' in campaign else None,
                                roas_bid=campaign["roas_bid"] if 'roas_bid' in campaign else None,
                                app_promotion_type=campaign[
                                    "app_promotion_type"] if 'app_promotion_type' in campaign else None
                            ))
            if update_campaign_data:
                Campaigns.objects.bulk_update(update_campaign_data,
                                              ['advertiser_id', 'is_new_structure', 'modify_time', 'campaign_id',
                                               'operation_status', 'objective', 'is_smart_performance_campaign',
                                               'budget_mode', 'budget', 'campaign_name', 'campaign_type', 'create_time',
                                               'rf_campaign_type', 'objective_type', 'secondary_status', 'roas_bid',
                                               'app_promotion_type'], batch_size=1000)
            if create_campaign_data:
                Campaigns.objects.bulk_create(create_campaign_data, batch_size=1000)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_campaign_by_advertiser(request, advertiser_id, access_token):
        response = {}
        try:
            # Args in JSON format
            path = "/campaign/get/"
            # Args in JSON format
            my_args = "{\"advertiser_id\": \"%s\" , \"page_size\":\"%s\"""}" % (advertiser_id, '1000')
            reports = tiktok_get(my_args, path, access_token)
            response["data"] = reports['data']['list']
            total_page = reports['data']['page_info']['total_page']
            page = reports['data']['page_info']['page']
            if total_page != page:
                for i in range(2, total_page + 1):
                    try:
                        page = i
                        my_args = "{\"advertiser_id\": \"%s\", \"page\":\"%s\", \"page_size\":\"%s\"}" % (
                            advertiser_id, page, '1000')
                        reports = tiktok_get(my_args, path, access_token)
                        response["data"] = response["data"] + reports['data']['list']
                    except Exception as e:
                        print("error", e)
                        continue
            response["success"] = True

        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
        return response

    def convert_datetime_timezone(tz):
        now_utc = datetime.now(timezone("UTC"))
        now_timezone = now_utc.astimezone(timezone(tz))
        dt = now_timezone.strftime("%Y-%m-%d")
        return dt

    def get_airtable_data(self):
        # print("-------------media_buyer start................")
        # media_buyer = AirtableView.get_airtable_media_buyer_data()  # Get media_buyer_data from airtable api.
        # new_media_buyer_response = AirtableView.save_media_buyer_into_db(media_buyer)
        # if 'new_media_buyer_data' in new_media_buyer_response:
        #     AirtableView.save_media_buyer_advertiser_into_db(new_media_buyer_response, media_buyer)
        # print("-------------media_buyer end................")
        print("-------------verticals start................")
        vertical_data = AirtableView.get_airtable_verticals_data()
        new_vertical_response = AirtableView.save_verticals_data_into_db(vertical_data)
        # if 'new_vertical_data' in new_vertical_response:
        #     AirtableView.save_vertical_advertiser_ids_into_db(new_vertical_response, vertical_data)
        print("-------------verticals end................")
        # print("-------------domain_data start................")
        # domain_data = AirtableView.get_airtable_domains_data()
        # print("domain_data---->", len(domain_data))
        # domain_data_obj = AirtableView.save_domains_data_into_db(domain_data)
        # AirtableView.save_advertiser_data_campaign_name(domain_data_obj)
        # print("-------------domain_data end................")
