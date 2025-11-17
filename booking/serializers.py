from rest_framework import serializers
from .models import Station, Booking, Payment
from django.utils import timezone

class StationSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Station
        fields = ["id", "name", "owner", "owner_name", "latitude", "longitude", "address", "created_at"]
        read_only_fields = ["id", "created_at", "owner_name"]

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    station_details = StationSerializer(source="station", read_only=True)
    time_remaining_seconds = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "user", "station", "station_details", "created_at", "expires_at", "time_remaining_seconds", "status", "amount", "meta"]
        read_only_fields = ["id", "created_at", "expires_at", "status", "time_remaining_seconds"]

    def get_time_remaining_seconds(self, obj):
        now = timezone.now()
        if obj.expires_at:
            diff = (obj.expires_at - now).total_seconds()
            return max(0, int(diff))
        return None

    def validate(self, data):
        # ensure station exists and is available at the requested time window (2 minutes)
        station = data.get("station") or getattr(self.instance, "station", None)
        if not station:
            raise serializers.ValidationError("Station is required.")

        # check overlapping confirmed bookings: we prevent booking if there's a confirmed booking active now
        from django.utils import timezone
        now = timezone.now()
        # active window: now .. now+2minutes
        window_end = now + timezone.timedelta(minutes=2)

        overlapping = Booking.objects.filter(
            station=station,
            status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
        ).filter(expires_at__gt=now)

        if overlapping.exists():
            raise serializers.ValidationError("Station already has an active booking. Try later.")

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        # set amount if not set (could be retrieved from station pricing)
        amount = validated_data.get("amount", 0.00)
        booking = Booking.objects.create(
            user=user,
            station=validated_data["station"],
            amount=amount,
            expires_at=timezone.now() + timezone.timedelta(minutes=2),
            meta=validated_data.get("meta", {})
        )
        return booking

class PaymentSerializer(serializers.ModelSerializer):
    booking_details = BookingSerializer(source="booking", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "booking", "booking_details", "amount", "gateway_order_id", "gateway_payment_id", "status", "created_at", "metadata"]
        read_only_fields = ["id", "created_at", "status", "gateway_order_id", "gateway_payment_id"]
