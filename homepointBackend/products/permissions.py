from rest_framework.permissions import BasePermission, SAFE_METHODS

class ReadOnly(BasePermission):
    """
    Allow read-only for users with role 'customer' or 'fundi'.
    """
    def has_permission(self, request, view=None):
        user = getattr(request, "user", None)
        role = getattr(user, "role", None)
        if role in ("customer", "fundi"):
            return request.method in SAFE_METHODS
        return False

class IsWarehouseStaff(BasePermission):
    """
    Allow access for authenticated users in the 'Warehouse Staff' group
    who have role 'staff' or 'admin'.
    """
    def has_permission(self, request, view=None):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        role = getattr(user, "role", None)
        if role in ("staff", "admin"):
            return user.groups.filter(name="Warehouse Staff").exists()
        return False

