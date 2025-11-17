from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class Users(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('evowner', 'EV Owner'),
        ('chargerowner', 'Charger Owner'),
    ]
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='evowner')
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"


# 🔹 OTP for password reset or other user operations
class EmailOTP(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"


# 🔹 OTP for Signup (before user is created)
from django.utils import timezone
from datetime import timedelta
from django.db import models
import pytz
class SignupOTP(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        now =  timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
        expiry_time = self.created_at.astimezone(pytz.timezone('Asia/Kolkata')) + timedelta(minutes=5)
        return now > expiry_time

    def __str__(self):
        return f"{self.email} - {self.code}"

