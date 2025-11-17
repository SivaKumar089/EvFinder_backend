from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Only the owner OR admin can modify.
    Everyone else has read-only access.
    """

    def has_object_permission(self, request, view, obj):
        # Allow GET, HEAD, OPTIONS to everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Admin can edit/delete
        if request.user and request.user.is_staff:
            return True

        # Owner can edit/delete
        return obj.owner == request.user
