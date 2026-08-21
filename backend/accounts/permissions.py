from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)


class IsOwnerOrInventoryManager(BasePermission):
    """Full read/write for Owner and Inventory Manager; read-only for Support."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_owner or request.user.is_inventory_manager


class ReadOnlyOrOwnerInventoryManager(BasePermission):
    """Alias kept for readability in viewsets that are explicitly read-mostly."""

    def has_permission(self, request, view):
        return IsOwnerOrInventoryManager().has_permission(request, view)
