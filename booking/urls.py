from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import  BookingViewSet, PaymentViewSet

router = DefaultRouter()
# router.register(r"stations", StationViewSet, basename="station")
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r'payments', PaymentViewSet, basename='payments')


urlpatterns = [
    path("", include(router.urls)),
]
