from rest_framework.routers import SimpleRouter
from django.conf.urls import url, include

from .views.manual_scheduler_view import ManualSchedulerView
from .views.scheduler_view import SchedulerView
from .views.titkok_bc import BCView
from .views.tonic_scheduler_view import TonicSchedulerView
from .views.monthly_scheduler_view import MonthlySchedulerView
from .views.users import UserViewSet, UserInfo
from .views.adveritsers import AdvertiserView
from .views.report import ReportView
# from .views.country_report import CountryReportView
from .views.partner import PartnerView
from .views.vertical import VerticalView

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
                  url(r'^auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
                  url(r'^user-profile/', UserInfo.as_view()),
                  # url(r'^tiktok/get-daily-advertisers/', AdvertiserView.get_daily_advertisers),
                  # url(r'^tiktok/get-daily-country-reports/', CountryReportView.get_daily_country_report),
                  # url(r'^tiktok/get-daily-partners/', PartnerView.get_daily_partners),
                  url(r'^tiktok/get-tiktok-data/', SchedulerView.get_scheduler_data),
                  url(r'^manual-tiktok/get-tiktok-data/', ManualSchedulerView.get_scheduler_data),
                  url(r'^tonic/get-tonic-data/', TonicSchedulerView.get_scheduler_data),
                  # url(r'^tonic/get_monthly_tonic_data/', MonthlySchedulerView.get_monthly_tonic_data),
                  url(r'^tonic/get-daily-tonic-data/', TonicSchedulerView.get_daily_tonic_data),
                  url(r'^products/', AdvertiserView.get_advertisers),
                  url(r'^total-report/', ReportView.get_total_report),
                  # url(r'^activity-report/', ReportView.get_activity_report),
                  url(r'^partners/', PartnerView.get_partners),
                  url(r'^verticals/', VerticalView.get_verticals),
                  url(r'^generate-csv/', AdvertiserView.generate_csv),
                  url(r'^hello/', AdvertiserView.hello),
                  url(r'^update-report/', AdvertiserView.save_reports_revenue),
                  url(r'^get-bc/', BCView.get_bc),
                  url(r'^daily-reports/', ReportView.get_daily_report),
                  # url(r'^country-report/', CountryReportView.as_view()),
                  # url(r'^email-verification/', UserInfo.email_verification),
                  # url(r'^resend-verification-code/', UserInfo.resend_verification_code),

              ] + router.urls
