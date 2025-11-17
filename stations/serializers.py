from rest_framework import serializers
from .models import Station, StationRating

class StationSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    owner_name = serializers.ReadOnlyField(source='owner.name')
    current_type = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = [
            'id', 'owner','owner_name', 'name', 'description',
            'latitude', 'longitude', 'type',
            'price', 'temp_type', 'temp_until',
            'is_active', 'created_at', 'current_type'
        ]

    def get_current_type(self, obj):
        return obj.current_type()


class StationRatingSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    station_name = serializers.ReadOnlyField(source='station.name')

    class Meta:
        model = StationRating
        fields = ['id', 'station', 'station_name', 'user', 'rating', 'comment', 'created_at']
