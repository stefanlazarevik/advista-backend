from django.views import generic
import logging
from django.conf import settings
import os, sys, time
import inspect

from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from collections import OrderedDict
from rest_framework.response import Response


class LogHelper(generic.DetailView):
    def elog(e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log = "----------- Error: " + str(exc_obj) + ", File: " + fname + ", Line: " + str(exc_tb.tb_lineno) + " ------------"
        print(log)
        logger = logging.getLogger(__name__)
        logger.debug(log)

    def ilog(value):
        try:
            (frame, filename, line_number,
             function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
            log = "----------- Info: " + str(value) +", File: " + str(os.path.split(filename)[1] + ", " + function_name + "()" + ", Line:" + str(line_number) + "]")
            logger = logging.getLogger(__name__)
            logger.debug(log)
            print(log)
        except Exception as e:
            print(e)

    def efail(e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log = "----------- Error: " + str(exc_obj) + ", File: " + fname + ", Line: " + str(
            exc_tb.tb_lineno) + " ------------"
        print(log)

    def warn(e):
        (frame, filename, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
        print("\r" + "[" + str(
            os.path.split(filename)[
                1] + ", " + function_name + "()" + ", Line:" + str(
                line_number) + "]"))
        print()

    def ex_time_init(msg=""):
        settings.EX_TIME = time.time()
        settings.EX_MSG = msg
        if msg != "":
            print("{} ==> {}".format(msg, str(time.time() - settings.EX_TIME)))

    def ex_time(*args, **kwargs):
        (frame, filename, line_number,
         function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
        print("{} ==> {}".format(settings.EX_MSG, str(time.time() - settings.EX_TIME) + "\t" + os.path.split(filename)[1] + " " + function_name + " " + str(line_number)))


class UserPermissions(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        limit = self.get_page_size(self.request)
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_page', int(self.page.paginator.count / limit) + (0 if (self.page.paginator.count % limit == 0) else 1)),
            ('results', data)
        ]))


class AdvertiserCalculateView(generic.DetailView):

    def get_status(request, advertiser):
        return advertiser.status_code
        # if advertiser.status == 'STATUS_ENABLE':
        #     return "active"
        # else:
        #     return "deactive"

    def get_total_cost(request, advertiser):
        try:
            return round(advertiser.total_cost, 2)
        except:
            return 0

    def get_revenue(request, advertiser):
        try:
            return round(advertiser.revenue, 2)
        except:
            return 0

    def get_conversion_rate(request, advertiser):
        try:
            return round(advertiser.conversions/(advertiser.clicks/100), 2)
        except:
            return 0.00

    def get_ctr(request, advertiser):
        try:
            return round((advertiser.clicks / advertiser.impressions) * 100, 2)
        except:
            return 0.00

    def get_cpm(request, advertiser):
        try:
            return round((advertiser.total_cost / advertiser.impressions) * 1000, 2)
        except:
            return 0.00

    def get_cpc(request, advertiser):
        try:
            return round((advertiser.total_cost / advertiser.clicks), 2)
        except:
            return 0.00

    def get_cpa(request, advertiser):
        try:
            return round((advertiser.total_cost / advertiser.conversions), 2)
        except:
            return 0.00

    def get_profit(request, advertiser):
        try:
            return round((advertiser.revenue - advertiser.total_cost), 2)
        except:
            return 0.00

    def get_roi(request, advertiser):
        try:
            return round((advertiser.revenue - advertiser.total_cost)/advertiser.total_cost * 100, 2)
        except:
            return 0.00
