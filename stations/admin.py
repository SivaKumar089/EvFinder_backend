from django.contrib import admin
from .models import Station, StationRating

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'get_base_type', 'price', 'is_active', 'created_at')
    search_fields = ('name', 'owner__username')

    # Method to show type in admin
    def get_base_type(self, obj):
        return obj.type  # Replace 'type' with the actual field name in your model
    get_base_type.short_description = 'Base Type'

@admin.register(StationRating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id','station','user','rating','created_at')
