from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from datetime import date, timedelta
from serviceapp.views.helper import LogHelper
from datetime import datetime

from .tonic_api import get_tonic_daily_report
from .tonic_scheduler_view import TonicSchedulerView
from ..models import TonicCampaignReports


class MonthlySchedulerView(APIView):
    # @api_view(["get"])
    # def get_monthly_tonic_data(request):
    #     response = {}
    #     start_date = None
    #     end_date = None
    #     try:
    #         print("---------------Month Start--------------")
    #         if "start_date" in request.GET:
    #             start_date = request.GET.get('start_date')
    #         if "end_date" in request.GET:
    #             end_date = request.GET.get('end_date')
    #         if start_date and end_date:
    #             start_date = datetime.strptime(start_date, '%Y-%m-%d')
    #             end_date = datetime.strptime(end_date, '%Y-%m-%d')
    #             # start_date = date(2008, 8, 15)
    #             # end_date = date(2008, 9, 15)  # perhaps date.now()
    #             delta = end_date - start_date  # returns timedelta
    #
    #             for i in range(delta.days + 1):
    #                 day = start_date + timedelta(days=i)
    #                 # _mutable = request.GET._mutable
    #                 # request.GET._mutable = True
    #                 # request.GET['today'] = day.date()
    #                 # request.GET._mutable = False
    #                 print(day.date())
    #                 token = TonicSchedulerView.get_tonic_api_token(request)
    #                 tonic_data = get_tonic_daily_report(day.date(), token)
    #                 MonthlySchedulerView.get_daily_tonic_data(request, tonic_data, day.date())
    #                 MonthlySchedulerView.get_scheduler_data(request, tonic_data, day.date())
    #             response["success"] = True
    #         else:
    #             response["success"] = False
    #             response["message"] = 'Enter start_date and end_date'
    #             return Response(response, status=status.HTTP_400_BAD_REQUEST)
    #         print("---------------Month END--------------")
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # def get_daily_tonic_data(request, tonic_data, timezone_date):
    #     response = {}
    #     create_tonic_data = []
    #     try:
    #         print("scheduler start-----------")
    #         LogHelper.ex_time_init("start Tonic")
    #         # if "today" in request.GET:
    #         #     timezone_date = request.GET.get('today')
    #         # else:
    #         #     timezone_date = TonicSchedulerView.convert_datetime_timezone("America/Los_Angeles")
    #         # print(timezone_date)
    #         # token = TonicSchedulerView.get_tonic_api_token(request)
    #         # tonic_data = get_tonic_daily_report(timezone_date, token)
    #         print("tonic_data-->", len(tonic_data))
    #         for data in tonic_data:
    #             create_tonic_data.append(TonicCampaignReports(
    #                 report_date=timezone_date,
    #                 revenue=data['revenueUsd'],
    #                 tonic_campaign_id=data['subid1'],
    #                 tonic_campaign_name=data['campaign_name'],
    #                 clicks=data['clicks'],
    #                 keyword=data['keyword'],
    #                 adtitle=data['adtitle'],
    #                 device=data['device'],
    #                 subid1=data['subid1'],
    #                 subid2=data['subid2'],
    #                 subid3=data['subid3'],
    #                 subid4=data['subid4'],
    #                 network=data['network'],
    #                 site=data['site']
    #             ))
    #         if create_tonic_data:
    #             TonicCampaignReports.objects.bulk_create(create_tonic_data, batch_size=1000)
    #         LogHelper.ex_time()
    #         print("scheduler end-----------")
    #         response["success"] = True
    #         return Response(response, status=status.HTTP_200_OK)
    #     except Exception as e:
    #         LogHelper.efail(e)
    #         response["success"] = False
    #         response["message"] = str(e)
    #         return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def get_scheduler_data(request, tonic_data, timezone_date):
        response = {}
        try:
            print("scheduler start-----------")
            LogHelper.ex_time_init("start Tonic")
            tonic_reports = TonicSchedulerView.get_tonic_report(request, tonic_data, timezone_date)
            LogHelper.ex_time()
            print("scheduler end-----------")
            response["success"] = True
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            LogHelper.efail(e)
            response["success"] = False
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
