"""
Custom permission classes for role-based access control.
"""

from rest_framework.permissions import BasePermission
from .models import UserProfile


def get_user_profile(user):
    """Safely retrieve a user's profile, or None if not found."""
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return None


class IsAdminRole(BasePermission):
    """Grants access only to users with the Admin role."""

    message = "You must have Admin role to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = get_user_profile(request.user)
        return profile is not None and profile.is_admin


class IsAnalystOrAdmin(BasePermission):
    """Grants access to Analyst or Admin roles."""

    message = "You must have Analyst or Admin role to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        profile = get_user_profile(request.user)
        return profile is not None and profile.can_view_analytics


class CanModifyRecords(BasePermission):
    """
    Only Admin users can create, update, or delete financial records.
    All authenticated users can read.
    """

    message = "You need Admin role to modify financial records."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read operations are allowed for all authenticated users
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Write operations require Admin role
        profile = get_user_profile(request.user)
        return profile is not None and profile.can_modify
