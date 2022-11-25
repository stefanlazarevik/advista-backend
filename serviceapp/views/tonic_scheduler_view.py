from pytz import timezone
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from serviceapp.models import Advertisers, Reports, Campaigns, CampaignReports
from rest_framework.decorators import api_view
from serviceapp.views.tiktok_api import tiktok_get
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
                                                                                                        set_campaign_id, timezone_date
                                                                                                        )
            print("create_campaign_reports->", len(create_campaign_reports))
            print("update_campaign_reports->", len(update_campaign_reports))
            if create_campaign_reports:
                CampaignReports.objects.bulk_create(create_campaign_reports)
            if update_campaign_reports:
                CampaignReports.objects.bulk_update(update_campaign_reports, ['revenue', 'clicks'])
            advertisers_list = TonicSchedulerView.get_advertisers_list(request)
            advertisers_campaign_objects = {
                advertiser_id: TonicSchedulerView.get_advertiser_campaign_list(request, advertiser_id) for
                advertiser_id in
                advertisers_list}
            advertiser_revenue_list = {
                i: TonicSchedulerView.get_advertiser_revenue(request, advertisers_campaign_objects[i], timezone_date)
                for i in advertisers_campaign_objects}
            advertiser_reveune = TonicSchedulerView.set_advertiser_reveune(request, advertiser_revenue_list,
                                                                            timezone_date)
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
                    if i['subid1'] == campaign:
                        revenue = revenue + float(i['revenueUsd'])
                        click = int(click) + int(i['clicks'])
                        i['revenueUsd'] = revenue
                        i['clicks'] = click
                        i['campaign_id'] = i['subid1']
                        if campaign not in result:
                            result[campaign] = i
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

    def get_advertisers_list(self):
        data_list = list(Advertisers.objects.values_list("advertiser_id", flat=True).all())
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
