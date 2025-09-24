from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows access to owners of an object or admin users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for owner or admin
        return (
            request.user.is_authenticated and (
                obj.user == request.user or request.user.is_staff
            )
        )


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows access to order owners or admin users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Order owners can access their orders
        return obj.user == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to authenticated users
    and write access only to admin users.
    """
    
    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for admin
        return request.user.is_authenticated and request.user.is_staff