"""
Root URL configuration for Finance Tracking System
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/summary/', include('analytics.urls')),
]
