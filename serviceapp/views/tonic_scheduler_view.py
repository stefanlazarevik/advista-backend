import json

from pytz import timezone
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Advertisers, Reports, Campaigns, CampaignReports, Domains, System1Revenue
from rest_framework.decorators import api_view

from serviceapp.views.airtable_api import AirtableView
from serviceapp.views.system1_api import get_system1_campaign_data
from serviceapp.views.helper import LogHelper
from datetime import datetime
from serviceapp.views.tonic_api import get_access_token, get_tonic_daily_report


class TonicSchedulerView(APIView):

    @api_view(["get"])
    def get_scheduler_data(request):
        response = {}
        try:
            print("scheduler start-----------")
            LogHelper.ex_time_init("start Tonic")
            tonic_reports = TonicSchedulerView.get_tonic_report(request)
            LogHelper.ex_time()
            print("scheduler end-----------")
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def convert_datetime_timezone(tz):
        now_utc = datetime.now(timezone("UTC"))
        now_timezone = now_utc.astimezone(timezone(tz))
        dt = now_timezone.strftime("%Y-%m-%d")
        print(dt)
        return dt

    def user_campaning_list(request):
        camping_list = list(Campaigns.objects.values_list("campaign_id", flat=True).all())
        # camping_list = [i.campaign_id for i in data]
        return camping_list

    def get_tonic_report(request):
        response = {}
        try:
            token = TonicSchedulerView.get_tonic_api_token(request)
            if "today" in request.GET:
                timezone_date = request.GET.get('today')
            else:
                timezone_date = TonicSchedulerView.convert_datetime_timezone("America/Los_Angeles")
            tonic_data = get_tonic_daily_report(timezone_date, token)
            print("tonic data--->", len(tonic_data))
            campaign_list = TonicSchedulerView.user_campaning_list(request)
            set_campaign_id = TonicSchedulerView.update_tonic_campaign_id(request, campaign_list, tonic_data)
            create_campaign_reports, update_campaign_reports = TonicSchedulerView.save_campign_resport(request,
                                                                                                       set_campaign_id,
                                                                                                       timezone_date)
            print("create_campaign_reports->", len(create_campaign_reports))
            print("update_campaign_reports->", len(update_campaign_reports))
            if create_campaign_reports:
                CampaignReports.objects.bulk_create(create_campaign_reports)
            if update_campaign_reports:
                CampaignReports.objects.bulk_update(update_campaign_reports, ['revenue', 'clicks'])
            get_system1_revenue_using_domain = TonicSchedulerView.get_system1_campaign_revenue(request,
                                                                                               timezone_date)
            if get_system1_revenue_using_domain:
                AirtableView.save_system1_campaign_revenue_into_db(get_system1_revenue_using_domain,
                                                                   timezone_date)
            get_reports_revenune = TonicSchedulerView.set_reports_revenue(request, tonic_data, timezone_date)
            if get_reports_revenune:
                TonicSchedulerView.save_reports_revenue(request, get_reports_revenune, timezone_date)
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
                click = 0
                for i in tonic_data:
                    data = {
                        'date': i['date'],
                        'campaign_id': i['campaign_id'],
                        'campaign_name': i['campaign_name'],
                        'clicks': i['clicks'],
                        'revenueUsd': i['revenueUsd'],
                        'subid1': i['subid1'],
                        'keyword': i['keyword'],
                        'adtitle': i['adtitle'],
                        'device': i['device'],

                    }
                    if data['subid1'] == campaign:
                        revenue = revenue + float(data['revenueUsd'])
                        click = int(click) + int(data['clicks'])
                        data['revenueUsd'] = revenue
                        data['clicks'] = click
                        data['campaign_id'] = data['subid1']
                        data['device'] = data['device']
                        if campaign not in result:
                            result[campaign] = data
                        else:
                            result[campaign]['revenueUsd'] = revenue
                            result[campaign]['clicks'] = click
        except Exception as e:
            print(e)
        return result

    def save_campign_resport(self, set_campaign_id, report_date):
        create_campaign_reports = []
        update_campaign_reports = []

        tonic_campaign_list = list(set_campaign_id.keys())
        existance_list = CampaignReports.objects.values_list('campaign_id', flat=True).filter(
            campaign_id__in=tonic_campaign_list, report_date=report_date)
        new_campaign = list(set(tonic_campaign_list).difference(existance_list))
        for i in tonic_campaign_list:
            data = set_campaign_id[i]
            if i in new_campaign:
                # Need to find optimize solution for this
                campaign = Campaigns.objects.filter(campaign_id=i).first()
                create_campaign_reports.append(CampaignReports(campaign_id=campaign, report_date=data['date'],
                                                               revenue=data['revenueUsd'],
                                                               tonic_campaign_id=data['subid1'],
                                                               tonic_campaign_name=data['campaign_name'],
                                                               clicks=data['clicks'],
                                                               keyword=data['keyword'], adtitle=data['adtitle'],
                                                               device=data['device']))
            else:
                campaign_reports = CampaignReports.objects.filter(campaign_id=i, report_date=report_date).first()
                if campaign_reports:
                    update_campaign_reports.append(
                        CampaignReports(
                            pk=campaign_reports.id,
                            report_date=data['date'],
                            revenue=data['revenueUsd'],
                            tonic_campaign_id=data['subid1'],
                            tonic_campaign_name=data['campaign_name'],
                            clicks=data['clicks'],
                            keyword=data['keyword'], adtitle=data['adtitle'],
                            device=data['device']))
        return create_campaign_reports, update_campaign_reports

    def set_reports_revenue(request, tonic_data, timezone_date):
        advertisers = TonicSchedulerView.get_advertisers_list(request)
        get_tonic_revenue = TonicSchedulerView.get_advertiser_tonic_revenune(request, advertisers, tonic_data,
                                                                             timezone_date)
        get_system1_revenue = TonicSchedulerView.get_advertiser_system1_revenue(request, timezone_date)
        commom = get_tonic_revenue.keys() & get_system1_revenue.keys()
        for i in get_tonic_revenue:
            if i in get_system1_revenue:
                get_tonic_revenue[i] = get_tonic_revenue[i] + get_system1_revenue[i]
        return get_tonic_revenue

    def get_advertisers_list(self):
        data_list = Advertisers.objects.values_list("advertiser_id", "tonic_campaign_name").all()
        # data_list = [i.advertiser_id for i in data]
        return data_list

    def get_advertiser_revenue(self, campaign_list, timezone_date):
        revenue = 0.0
        if campaign_list:
            result = CampaignReports.objects.filter(campaign_id__in=campaign_list,
                                                    report_date=timezone_date).aggregate(Sum('revenue'))['revenue__sum']
            if result:
                revenue = round(result, 2)
            else:
                revenue = 0.0
        return revenue

    def get_advertiser_campaign_list(self, advertiser_id):
        data_list = list(Campaigns.objects.values_list("campaign_id", flat=True).filter(advertiser_id=advertiser_id))
        return data_list

    def set_advertiser_reveune(self, advertiser_revenue_list, timezone_date):
        print("date--->", timezone_date)
        try:
            update_list = []
            for advertiser in advertiser_revenue_list:
                reports = Reports.objects.filter(advertiser_id=advertiser, report_date=timezone_date).first()
                if reports:
                    revenue = advertiser_revenue_list[advertiser]
                    update_list.append(Reports(pk=reports.pk, revenue=revenue))
            if update_list:
                len(update_list)
                response = Reports.objects.bulk_update(update_list, ['revenue'])
            return True
        except Exception as e:
            return False

    def get_advertiser_tonic_revenune(self, advertiser, tonic_data, timezone_date):
        total_revenue = {}
        subid_revenue = {}
        advertisers_list = {i[1]: i[0] for i in advertiser}
        advertisers_campaign_objects = {
            adv[0]: TonicSchedulerView.get_advertiser_campaign_list(self, adv[0]) for
            adv in advertiser
        }
        revenue_list = {}
        for i in tonic_data:
            if i['subid1'] is None:
                if i['campaign_name'] in (list(advertisers_list.keys())):
                    advertiser_id = advertisers_list[i['campaign_name']]
                    revenue = i['revenueUsd']
                    if advertiser_id in revenue_list:
                        revenue_list[advertiser_id]['revenue'] = revenue_list[advertiser_id]['revenue'] + float(revenue)
                    else:
                        revenue_list[advertiser_id] = {
                            "revenue": float(revenue)
                        }
            else:
                id = i['subid1']
                if id in subid_revenue:
                    subid_revenue[id] = subid_revenue[id] + float(i['revenueUsd'])
                else:
                    subid_revenue[id] = float(i['revenueUsd'])
        for adver in advertisers_campaign_objects:
            revenue = revenue_list[adver]['revenue'] if adver in revenue_list else 0
            campaign_list = advertisers_campaign_objects[adver]
            for campaign in campaign_list:
                if campaign in subid_revenue:
                    revenue = revenue + subid_revenue[campaign]
            total_revenue[adver] = round(revenue, 2)
        return total_revenue

    def get_system1_campaign_revenue(self, date):
        domains_data = Domains.objects.all().prefetch_related('advertiser_id')
        result = {}
        for i in domains_data:
            data = i
            if data.source == 'System1':
                domain = \
                    data.partner_url.replace('http://', '').replace("/", '').replace(":", "").replace("https",
                                                                                                      "").split(
                        "?rskey")[0]
                advertiser_id = data.advertiser_id.advertiser_id.strip()
                result[domain] = {
                    'advertiser_id': advertiser_id,
                    'domain_id': data.domain_id
                }
        domain_list = list(result.keys())
        campaign = ','.join(domain_list)
        params = {
            'days': date,
            'campaign': campaign
        }
        get_system1_campaign = get_system1_campaign_data(params)
        system1_obj = {}
        for i in get_system1_campaign[1:]:
            domain = i[1]
            if domain:
                revenue = i[12]
                clicks = i[11]
                revenue_per_click = i[16]
                if domain in system1_obj:
                    system1_obj[domain]['revenue'] = system1_obj[domain]['revenue'] + float(revenue)
                    system1_obj[domain]['clicks'] = system1_obj[domain]['clicks'] + clicks
                    system1_obj[domain]['revenue_per_click'] = system1_obj[domain]['revenue_per_click'] + float(
                        revenue_per_click)
                else:
                    system1_obj[domain] = {
                        'report_date': date,
                        'clicks': i[11],
                        'revenue': i[12],
                        'revenue_per_click': i[16],
                    }
        for i in system1_obj:
            try:
                advertiser = result[i]['advertiser_id']
                system1_obj[i]['advertiser_id'] = advertiser
                system1_obj[i]['domain_id'] = result[i]['domain_id']
            except Exception as e:
                continue
        return system1_obj

    def get_advertiser_system1_revenue(self, timezone_date):
        system1_revenue = System1Revenue.objects.values_list('advertiser_id', 'revenue').filter(
            report_date=timezone_date)
        result = {i[0]: i[1] for i in system1_revenue}
        return result

    def save_reports_revenue(self, get_reports_revenune, timezone_date):
        update_list = []
        for i in get_reports_revenune:
            try:
                report = Reports.objects.get(advertiser_id=i, report_date=timezone_date)
                update_list.append(Reports(pk=report.id, revenue=get_reports_revenune[i]))
            except Exception as e:
                continue

        if update_list:
            print("update-report-table", len(update_list))
            Reports.objects.bulk_update(update_list, ['revenue'], batch_size=100)
