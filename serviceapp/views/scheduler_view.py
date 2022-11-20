import json
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
            tonic_reports = SchedulerView.get_tonic_report(request)
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
            advertiser_list = []
            advertiser_data = {}
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
                advertiser_data[advertiser['advertiser_id']] = advertiser_dict
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

    def convert_datetime_timezone(tz):
        now_utc = datetime.now(timezone("UTC"))
        now_timezone = now_utc.astimezone(timezone(tz))
        dt = now_timezone.strftime("%Y-%m-%d")
        return dt

    def user_campaning_list(request):
        data = Campaigns.objects.all()
        camping_list = [i.campaign_id for i in data]
        return camping_list

    def get_tonic_report(request):
        response = {}
        try:
            token = SchedulerView.get_tonic_api_token(request)
            # token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkbG4iOiJGVWZXcU1Sd3pRX2dPdGR3M1I2QlhGWkZ4NENIY3NhaTk0RFVrV2EzVXpqVDVpTWFkRWN3UzlWbTFjNEFUMmJVejVhR0NqcWd4bFFaOV9fY0FoS1V5ZEc1S19vU0dtMm5wcTRRZWFMX0o3blNKVVRPaTNFVXF6ZU9GVEZHZXc0NUVRSGhId2FwSlI1M3NRODdWQmNPNTdKVEdqcTQ5QUlBcm9ERWR1OGQyck0iLCJleHAiOjE2Njg3MTA2MTl9.pt8mT4Uwzuqj7qRYP6R7WYqaY_ImcpGYBNSqmX-l8S0'
            tonic_data = get_tonic_daily_report(token)
            campign_list = SchedulerView.user_campaning_list(request)
            set_campaign_id = SchedulerView.update_tonic_campaign_id(request, campign_list, tonic_data)

            create_campaign_reports, update_campaign_reports = SchedulerView.save_campign_resport(request,
                                                                                                  set_campaign_id)
            if create_campaign_reports:
                CampaignReports.objects.bulk_create(create_campaign_reports)
            if update_campaign_reports:
                CampaignReports.objects.bulk_update(create_campaign_reports, ['revenue'])
            advertisers_list = SchedulerView.get_advertisers_list(request)
            advertisers_campaign_objects = {
                advertiser_id: SchedulerView.get_advertiser_campaign_list(request, advertiser_id) for advertiser_id in
                advertisers_list}
            advertiser_revenue_list = {i: SchedulerView.get_advertiser_revenue(request, advertisers_campaign_objects[i])
                                       for i in advertisers_campaign_objects}
            advertiser_reveune = SchedulerView.set_advertiser_reveune(request, advertiser_revenue_list)
            # print(advertiser_reveune)
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_tonic_api_token(request):
        data = get_access_token().json()
        return data['token']

    def update_tonic_campaign_id(self, campaign_list, tonic_data):
        result = {}
        try:
            for campaign in campaign_list:
                revenue = 0.0
                for i in tonic_data:
                    if i['tonic_campaign_id'] == campaign:
                        revenue = round(revenue + float(i['revenue']), 2)
                        i['revenue'] = revenue
                        i['campaign_id'] = i['tonic_campaign_id']

                        if campaign not in result:
                            result[campaign] = i
                        else:
                            result[campaign]['revenue'] = revenue
        except Exception as e:
            print(e)
        return result

    def save_campign_resport(self, set_campaign_id):
        create_campaign_reports = []
        update_campaign_reports = []
        for i in set_campaign_id:
            data = set_campaign_id[i]
            campaign = Campaigns.objects.get(campaign_id=i)
            campaign_reports = CampaignReports.objects.filter(campaign_id=campaign).first()
            if campaign_reports is None:
                create_campaign_reports.append(CampaignReports(campaign_id=campaign, report_date=data['report_date'],
                                                               revenue=data['revenue'],
                                                               tonic_campaign_id=data['tonic_campaign_id'],
                                                               tonic_campaign_name=data['tonic_campaign_name'],
                                                               clicks=data['clicks'],
                                                               keyword=data['keyword'], adtitle=data['adtitle'],
                                                               device=data['device']))
            else:
                update_campaign_reports.append(
                    CampaignReports(id=campaign_reports.id, campaign_id=campaign, report_date=data['report_date'],
                                    revenue=data['revenue'],
                                    tonic_campaign_id=data['tonic_campaign_id'],
                                    tonic_campaign_name=data['tonic_campaign_name'],
                                    clicks=data['clicks'],
                                    keyword=data['keyword'], adtitle=data['adtitle'],
                                    device=data['device']))
        return create_campaign_reports, update_campaign_reports

    def get_advertisers_list(self):
        data = Advertisers.objects.all()
        data_list = [i.advertiser_id for i in data]
        return data_list

    def get_advertiser_revenue(self, campaign_list):
        result = {}
        if campaign_list:
            data = CampaignReports.objects.filter(campaign_id__in=campaign_list)
            for i in data:
                date = i.report_date.strftime("%Y-%m-%d")
                if date in result:
                    result[date] = round(result[date] + float(i.revenue), 2)
                else:
                    result[date] = i.revenue
                    # revenue = round(revenue + float(i.revenue), 2)
        return result

    def get_advertiser_campaign_list(self, advertiser_id):
        data = Campaigns.objects.filter(advertiser_id=advertiser_id)
        data_list = [i.campaign_id for i in data]
        return data_list

    def set_advertiser_reveune(self, advertiser_revenue_list):
        count = 0
        for advertiser in advertiser_revenue_list:
            date_list = advertiser_revenue_list[advertiser]
            for date in date_list:
                try:
                    revenue = date_list[date]
                    reports = Reports.objects.filter(advertiser_id=advertiser, report_date=date)
                    if reports:
                        try:
                            for i in reports:
                                # print(advertiser, date)
                                # print(i.advertiser_id.advertiser_id, i.report_date)
                                # print('-------------------')
                                i.revenue = revenue
                                i.save()
                                count = count + 1
                        except Exception as e:
                            continue
                except Exception as e:
                    print(e)
                    continue
        return count
