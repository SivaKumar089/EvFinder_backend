from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Station, Booking, Payment
from .serializers import StationSerializer, BookingSerializer, PaymentSerializer
from .permissions import IsEvUser, IsEvOwnerOrAdmin
import uuid

# class StationViewSet(viewsets.ModelViewSet):
#     """
#     Station CRUD — only owners/admins can create/update/destroy.
#     List and retrieve allowed for all authenticated users.
#     """
#     queryset = Station.objects.all()
#     serializer_class = StationSerializer

#     def get_permissions(self):
#         if self.action in ("create", "update", "partial_update", "destroy"):
#             return [IsAuthenticated(), IsEvOwnerOrAdmin()]
#         return [IsAuthenticated()]

#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)

class BookingViewSet(viewsets.ModelViewSet):
    """
    Booking endpoints:
      - create booking (user only) => PENDING (expires in 2 min)
      - confirm payment: /booking/{pk}/pay/ -> create Payment and mark BOOKING as CONFIRMED
      - list user bookings (history)
    """
    queryset = Booking.objects.select_related("station", "user").all().order_by("-created_at")
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action in ("create", "pay", "my_bookings"):
            return [IsAuthenticated(), IsEvUser()]
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        # return all for admin; normal users get their own bookings
        user = self.request.user
        qs = super().get_queryset()
        role = getattr(user, "role", None)
        if role in ("admin",):
            return qs
        return qs.filter(user=user)

    @action(detail=True, methods=["POST"], url_path="fake-pay")
    def pay(self, request, pk=None):
        """
        Fake Razorpay flow:
          1) Client calls /booking/{id}/fake-pay/ to create a fake payment order
             Server creates a Payment object in CREATED state and returns gateway_order_id
          2) Client simulates success by calling /payment/{id}/confirm/ (or we can confirm here)
        For simplicity, here we will create payment and optionally confirm if `confirm=true`.
        """
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        # check expiry
        booking.mark_expired_if_needed()
        if booking.status == Booking.STATUS_EXPIRED:
            return Response({"detail": "Booking expired."}, status=status.HTTP_400_BAD_REQUEST)
        if booking.status == Booking.STATUS_CONFIRMED:
            return Response({"detail": "Booking already confirmed."}, status=status.HTTP_400_BAD_REQUEST)

        # create fake payment
        fake_order_id = f"fake_order_{uuid.uuid4().hex[:12]}"
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.amount or 0.00,
            gateway_order_id=fake_order_id,
            status=Payment.STATUS_CREATED
        )

        # optional: if client passed confirm=true -> mark paid immediately
        confirm = request.data.get("confirm", False)
        if confirm in (True, "true", "True", "1", 1):
            payment.gateway_payment_id = f"fake_pay_{uuid.uuid4().hex[:12]}"
            payment.status = Payment.STATUS_PAID
            payment.save(update_fields=["gateway_payment_id", "status"])
            # mark booking confirmed
            booking.status = Booking.STATUS_CONFIRMED
            booking.save(update_fields=["status"])
            return Response({"payment_order_id": fake_order_id, "payment_id": payment.gateway_payment_id, "status": payment.status}, status=status.HTTP_200_OK)

        return Response({"payment_order_id": fake_order_id, "payment_id": None, "status": payment.status}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["GET"], url_path="my-bookings")
    def my_bookings(self, request):
        user = request.user
        qs = self.get_queryset().filter(user=user).order_by("-created_at")
        # expire bookings where needed before serialization
        for b in qs:
            b.mark_expired_if_needed()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payment endpoints: confirm payment for a given payment id (fake).
    Admin can list all payments; users can see their own.
    """
    queryset = Payment.objects.select_related("booking", "booking__user").all().order_by("-created_at")
    serializer_class = PaymentSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        role = getattr(user, "role", None)
        if role in ("admin",):
            return super().get_queryset()
        return self.queryset.filter(booking__user=user)

    @action(detail=True, methods=["POST"], url_path="confirm")
    def confirm(self, request, pk=None):
        payment = self.get_object()
        booking = payment.booking
        # mark expired if needed
        booking.mark_expired_if_needed()
        if booking.status == Booking.STATUS_EXPIRED:
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status"])
            return Response({"detail": "Booking expired; payment failed."}, status=status.HTTP_400_BAD_REQUEST)

        # simulate verification of gateway (we skip signatures)
        payment.gateway_payment_id = f"fake_pay_{uuid.uuid4().hex[:12]}"
        payment.status = Payment.STATUS_PAID
        payment.save(update_fields=["gateway_payment_id", "status"])

        # mark booking confirmed
        booking.status = Booking.STATUS_CONFIRMED
        booking.save(update_fields=["status"])

        return Response({"detail": "Payment confirmed, booking reserved.", "payment_id": payment.gateway_payment_id}, status=status.HTTP_200_OK)
