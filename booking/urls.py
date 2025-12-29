from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import  BookingViewSet, PaymentViewSet,OwnerStationSummaryView,StationBookingList

router = DefaultRouter()
# router.register(r"stations", StationViewSet, basename="station")
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r'payments', PaymentViewSet, basename='payments')


urlpatterns = [
    path("", include(router.urls)),
    path("summary/", OwnerStationSummaryView.as_view(), name="owner-station-summary"),
    path("bookings/stations/<int:station_id>/", StationBookingList.as_view()),


]
