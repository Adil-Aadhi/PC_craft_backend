from rest_framework.permissions import BasePermission

class IsApprovedWorker(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return (
            user.is_authenticated and
            user.role == "worker" and
            hasattr(user, "worker_profile") and
            user.worker_profile.kyc_status == "approved"
        )
