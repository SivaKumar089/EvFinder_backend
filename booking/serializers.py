from rest_framework import serializers
from .models import Booking


from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    # station_id = serializers.UUIDField(source="station.id", read_only=True)
    station_name = serializers.CharField(source="station.name", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "station",          # <== write-only input
            # "station_id",
            "station_name",
            "user_id",
            "user_name",
            "amount",
            "status",
            "created_at",
            "expires_at",
        ]

        extra_kwargs = {
            "station": {"write_only": True, "required": True},  # <== IMPORTANT FIX
            "status": {"read_only": True},
            "created_at": {"read_only": True},
            "expires_at": {"read_only": True},
        }


from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)
    station_name = serializers.CharField(source="booking.station.name", read_only=True)
    user_id = serializers.IntegerField(source="booking.user.id", read_only=True)
    user_name = serializers.CharField(source="booking.user.username", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "booking_id",
            "station_name",
            "user_id",
            "user_name",

            "amount",
            

            "gateway_order_id",
            "gateway_payment_id",
            "status",

            "created_at"
        ]

        read_only_fields = [
            "id",
            "booking_id",
            "station_name",
            "user_id",
            "user_name",
            "created_at"
        ]
