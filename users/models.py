"""
Users app models.

Extends Django's default User model with a role field
to support Viewer, Analyst, and Admin access levels.
"""

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends the built-in Django User with a role field.
    One-to-one relationship ensures each user has exactly one profile.
    """

    class Role(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        ANALYST = 'analyst', 'Analyst'
        ADMIN = 'admin', 'Admin'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_analyst(self):
        return self.role == self.Role.ANALYST

    @property
    def is_viewer(self):
        return self.role == self.Role.VIEWER

    @property
    def can_modify(self):
        """Only admins can create, update, or delete records."""
        return self.role == self.Role.ADMIN

    @property
    def can_view_analytics(self):
        """Analysts and Admins can access analytics features."""
        return self.role in (self.Role.ANALYST, self.Role.ADMIN)
