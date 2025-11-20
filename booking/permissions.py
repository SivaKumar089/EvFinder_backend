from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsEvUser(BasePermission):
    """
    Allows access only to EV users (role = 'user').
    Used for: Booking create, fake pay, my bookings.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated and 
            getattr(user, "role", None) == "evowner"
        )


class IsEvOwnerOrAdmin(BasePermission):
    """
    Allows access only to station owners or admin.
    Used for: Station CRUD
    """
    def has_permission(self, request, view):
        user = request.user
        role = getattr(user, "role", None)

        if not user.is_authenticated:
            return False

        # Owners & Admin have full access
        if role in ("chargerowner", "admin"):
            return True

        # Safe methods allowed for all authenticated users
        if request.method in SAFE_METHODS:
            return True

        return False


class IsAdmin(BasePermission):
    """
    Only admin can access this endpoint.
    """
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated and 
            getattr(request.user, "role", None) == "admin"
        )
