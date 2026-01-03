from rest_framework.permissions import BasePermission, SAFE_METHODS

class ReadOnly(BasePermission):
    """
    Custom: Allow read-only for anyone
    """
    def has_permission(self, request):
        return request.method in SAFE_METHODS

class IsWarehouseStaff(BasePermission):
    """
    Future: Allow if user is in 'Warehouse Staff' group.
    """
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='Warehouse Staff').exists()
    
