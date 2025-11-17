from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Station, StationRating
from .serializers import StationSerializer, StationRatingSerializer
from .permissions import IsOwnerOrReadOnly




class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']


    def get_queryset(self):
        user = self.request.user

        # Admin → see all
        if user.is_authenticated and user.is_staff:
            return Station.objects.all()

        # EV Owner → only active stations
        if user.is_authenticated and getattr(user, "role", None) == "evowner":
            return Station.objects.filter(is_active=True)

        # Charger Owner → only his stations
        if user.is_authenticated and getattr(user, "role", None) == "chargerowner":
            return Station.objects.filter(owner=user)

        # Public users
        return Station.objects.filter(is_active=True)

    # Assign owner automatically on create
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # -----------------------------
    # CUSTOM ACTIONS
    # -----------------------------

    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def set_price(self, request, pk=None):
        station = self.get_object()

        # Only owner or admin can update the price
        if request.user != station.owner and not request.user.is_staff:
            return Response({'error': 'Not allowed'}, status=403)

        price = request.data.get('price')

        if price is None:
            return Response({'error': 'Price is required'}, status=400)

        try:
            price = float(price)
        except ValueError:
            return Response({'error': 'Price must be numeric'}, status=400)

        station.price = price
        station.save()

        return Response({
            'detail': 'Price updated successfully',
            'price': price
        }, status=200)

    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def set_temp_type(self, request, pk=None):
        station = self.get_object()

        if request.user != station.owner:
            return Response({'error': 'Not allowed'}, status=403)

        type = request.data.get('type')

        allowed = ['bike', 'car', 'both', None, '']

        if type not in allowed:
            return Response({"error": "Invalid type"}, status=400)

        station.type = type if type else None
        station.save()

        return Response({
            "detail": "type updated",
            "type": station.type
        })

    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def set_active(self, request, pk=None):
        station = self.get_object()

        if request.user != station.owner:
            return Response({'error': 'Not allowed'}, status=403)

        active = request.data.get('is_active')
        station.is_active = str(active).lower() in ['true', '1', 'yes']
        station.save()

        return Response({'detail': 'Active flag updated', 'is_active': station.is_active})
    
    
    



    @action(detail=True, methods=['put'], permission_classes=[permissions.IsAuthenticated])
    def set_location(self, request, pk=None):
        station = self.get_object()

        # Only station owner OR admin can update
        if request.user != station.owner:
            return Response({'error': 'Not allowed'}, status=403)

        lat = request.data.get("latitude")
        lng = request.data.get("longitude")

        if lat is None or lng is None:
            return Response({"error": "Both latitude and longitude are required"}, status=400)

        # Validate numeric
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response({"error": "Latitude and Longitude must be numeric"}, status=400)

        # DB update
        station.latitude = lat
        station.longitude = lng
        station.save()

        return Response({
            "detail": "Location updated successfully",
            "latitude": station.latitude,
            "longitude": station.longitude
        }, status=200)



class StationRatingViewSet(viewsets.ModelViewSet):
    queryset = StationRating.objects.all()
    serializer_class = StationRatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
