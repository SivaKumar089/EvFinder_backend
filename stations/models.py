from django.db import models
from users.views import Users
from django.utils import timezone

class Station(models.Model):
    TYPE_BIKE = 'bike'
    TYPE_CAR = 'car'
    TYPE_BOTH = 'both'

    TYPE_CHOICES = [
        (TYPE_BIKE, 'Bike'),
        (TYPE_CAR, 'Car'),
        (TYPE_BOTH, 'Both'),
    ]

    owner = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='stations')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_BOTH)

    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    temp_type = models.CharField(max_length=10, choices=TYPE_CHOICES, blank=True, null=True)
    temp_until = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def current_type(self):
        """
        Return the current type considering temp_type and temp_until.
        Automatically clear expired temp_type.
        """
        if self.temp_until and timezone.now() > self.temp_until:
            self.temp_type = None
            self.temp_until = None
            self.save(update_fields=['temp_type', 'temp_until'])
        return self.temp_type or self.type

    def __str__(self):
        return f"{self.name} ({self.current_type()})"


class StationRating(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=1)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('station', 'user')

    def __str__(self):
        return f"{self.station.name} - {self.rating}"
