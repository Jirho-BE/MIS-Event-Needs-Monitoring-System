from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        #Make sure to always make Admin user ID as 1
        return bool(request.user and request.user.is_authenticated and request.user.id == 1)

class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.id == 1:
            return True
        return request.user == obj