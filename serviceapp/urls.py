from rest_framework.routers import SimpleRouter
from django.conf.urls import url, include
from .views.users import UserViewSet, UserInfo
from .views.adveritsers import AdvertiserView
from .views.report import ReportView
from .views.country_report import CountryReportView
from .views.partner import PartnerView

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    url(r'^auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^user-profile/', UserInfo.as_view()),
    url(r'^tiktok/get-daily-advertisers/', AdvertiserView.get_daily_advertisers),
    url(r'^tiktok/get-daily-reports/', ReportView.get_daily_report),
    url(r'^tiktok/get-daily-country-reports/', CountryReportView.get_daily_country_report),
    url(r'^tiktok/get-daily-partners/', PartnerView.get_daily_partners),
    # url(r'^email-verification/', UserInfo.email_verification),
    # url(r'^resend-verification-code/', UserInfo.resend_verification_code),

] + router.urls

