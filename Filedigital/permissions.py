from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow only the file owner or admin (superuser/staff)
        return request.user.is_staff or obj.uploaded_by == request.user