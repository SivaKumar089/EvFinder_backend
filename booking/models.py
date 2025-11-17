from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

User = settings.AUTH_USER_MODEL



class Booking(models.Model):
    STATUS_PENDING = "PENDING"     # created, awaiting payment confirmation
    STATUS_CONFIRMED = "CONFIRMED" # payment done & booking reserved
    STATUS_EXPIRED = "EXPIRED"     # not paid within 2 minutes (or time passed)
    STATUS_CANCELLED = "CANCELLED"
    STATUS_COMPLETED = "COMPLETED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="bookings")
    created_at = models.DateTimeField(auto_now_add=True)
    # booking reserved for 2 minutes from created_at
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    meta = models.JSONField(null=True, blank=True)  # any extra data (count, vehicle type ...)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # amount to pay

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(minutes=2) if self.created_at else timezone.now() + timedelta(minutes=2)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at and self.status in (self.STATUS_PENDING,)

    def mark_expired_if_needed(self):
        if self.is_expired():
            self.status = self.STATUS_EXPIRED
            self.save(update_fields=["status"])

    def __str__(self):
        return f"Booking {self.id} by {self.user}"

class Payment(models.Model):
    STATUS_CREATED = "CREATED"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"
    STATUS_REFUNDED = "REFUNDED"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    gateway_order_id = models.CharField(max_length=200, blank=True, null=True)  # fake order id
    gateway_payment_id = models.CharField(max_length=200, blank=True, null=True)  # fake payment id
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} ({self.status})"
