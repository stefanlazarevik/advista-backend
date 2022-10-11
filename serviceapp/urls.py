from rest_framework.routers import SimpleRouter
from django.conf.urls import url, include
from .views.users import UserViewSet, UserInfo

router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    url(r'^auth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^user-profile/', UserInfo.as_view()),

] + router.urls

