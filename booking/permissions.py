from rest_framework import permissions

class IsEvUser(permissions.BasePermission):
    """
    Allow only authenticated users who are EV users (role 'user' or 'ev_user').
    Adjust role strings to match your project.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        return role in ("user", "ev_user", "customer") or role is None and user.is_authenticated

class IsEvOwnerOrAdmin(permissions.BasePermission):
    """
    Allow only station owner / admin to perform certain actions (e.g., create station).
    Adjust role strings to match your project.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        return role in ("owner", "ev_owner", "admin")
