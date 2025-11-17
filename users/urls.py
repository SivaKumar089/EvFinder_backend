from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    SignupSendOTPView,
    SignupVerifyOTPView,
    LoginView,
    LogoutView,
    forgot_password,
    send_otp,
    verify_otp
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('signup', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path("signup-send-otp/", SignupSendOTPView.as_view(), name="signup-send-otp"),
    path("emailverify-otp/", SignupVerifyOTPView.as_view(), name="emailverify-otp"),
    path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
