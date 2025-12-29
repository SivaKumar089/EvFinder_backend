from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import uuid
from django.utils import timezone

from .models import Booking
from .serializers import BookingSerializer
from .permissions import IsEvUser
from .models import Payment


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related("station", "user").all().order_by("-created_at")
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action in ("create", "fake_pay", "my_bookings"):
            return [IsAuthenticated(), IsEvUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # Owner → Avan own panna station bookings mattum
        if user.role == "chargerowner":
            qs = qs.filter(station__owner=user)
        else:
            qs = qs.filter(user=user)

        station_id = self.request.query_params.get('station_id')
        if station_id and station_id.isdigit():
            qs = qs.filter(station_id=station_id)

        return qs



    @action(detail=True, methods=["POST"], url_path="fake-pay")
    def fake_pay(self, request, pk=None):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)

        booking.mark_expired_if_needed()
        if booking.status == Booking.STATUS_EXPIRED:
            return Response({"detail": "Booking expired."}, status=400)

        if booking.status == Booking.STATUS_CONFIRMED:
            return Response({"detail": "Already paid & confirmed."}, status=400)

        fake_order_id = f"fake_order_{uuid.uuid4().hex[:12]}"

        payment = Payment.objects.create(
            booking=booking,
            amount=booking.amount,
            gateway_order_id=fake_order_id,
            status=Payment.STATUS_CREATED
        )

        confirm = request.data.get("confirm", False)

        if str(confirm).lower() in ("true", "1"):
            payment.gateway_payment_id = f"fake_pay_{uuid.uuid4().hex[:12]}"
            payment.status = Payment.STATUS_PAID
            payment.save()

            booking.status = Booking.STATUS_CONFIRMED
            booking.save(update_fields=["status"])

            return Response({
                "payment_order_id": payment.gateway_order_id,
                "payment_id": payment.gateway_payment_id,
                "amount": payment.amount,
                "status": "PAID"
            }, status=200)

        return Response({
            "payment_order_id": fake_order_id,
            "payment_id": None,
            "status": "CREATED"
        }, status=201)

    @action(detail=False, methods=["GET"], url_path="my-bookings")
    def my_bookings(self, request):
        qs = self.get_queryset().filter(user=request.user)
        for b in qs:
            b.mark_expired_if_needed()

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
 

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import uuid

from .models import Payment
from booking.models import Booking
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    # queryset = Payment.objects.select_related("booking", "booking__station").all()        
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        if user.role == "owner":
            return Payment.objects.all()
        return Payment.objects.filter(booking__user=user)
    
    @action(detail=False, methods=["POST"], url_path="create")
    def create_payment(self, request):

        booking_id = request.data.get("booking_id")
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        booking.mark_expired_if_needed()
        if booking.status == Booking.STATUS_EXPIRED:
            return Response({"detail": "Booking expired"}, status=400)

        fake_order_id = f"fake_order_{uuid.uuid4().hex[:10]}"

        payment = Payment.objects.create(
            booking=booking,
            amount=booking.amount,
            gateway_order_id=fake_order_id,
            status=Payment.STATUS_CREATED
        )

        return Response({
            "payment_id": payment.id,
            "order_id": fake_order_id,
            "amount": payment.amount,
            "status": "CREATED"
        }, status=201)

    @action(detail=True, methods=["POST"], url_path="confirm")
    def confirm(self, request, pk=None):
        payment = self.get_object()
        booking = payment.booking

        booking.mark_expired_if_needed()
        if booking.status == Booking.STATUS_EXPIRED:
            payment.status = Payment.STATUS_FAILED
            payment.save()
            return Response({"detail": "Booking expired. Payment failed."}, status=400)

        payment.gateway_payment_id = f"fake_pay_{uuid.uuid4().hex[:10]}"
        payment.status = Payment.STATUS_PAID
        payment.save()

        booking.status = Booking.STATUS_CONFIRMED
        booking.save()

        return Response({
            "detail": "Payment Success",
            "payment_id": payment.gateway_payment_id,
            "amount": payment.amount,
            "station": booking.station.name,
            "status": "PAID"
        }, status=200)




from django.db.models import Count, Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class OwnerStationSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.role != "chargerowner":
            return Response({"detail": "Not allowed"}, status=403)

        data = (
            Booking.objects
            .filter(station__owner=user)
            .values("station__id", "station__name")
            .annotate(
                total_bookings=Count("id"),
                paid_bookings=Count("id", filter=Q(status="CONFIRMED")),
                pending_bookings=Count("id", filter=Q(status="PENDING")),
                expired_bookings=Count("id", filter=Q(status="EXPIRED")),
                total_revenue=Sum("amount", filter=Q(status="CONFIRMED"))
            )
            .order_by("-total_bookings")
        )

        return Response(data)



class StationBookingList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, station_id):
        user = request.user
        
        # Ensure owner access
        if user.role != "chargerowner":
            return Response({"detail": "Not allowed"}, status=403)

        qs = Booking.objects.filter(station__id=station_id, station__owner=user)

        serializer = BookingSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
