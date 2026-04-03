"""
URL routes for the transactions app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction-list'),
    path('filter/', views.transaction_filter, name='transaction-filter'),
    path('<int:transaction_id>/', views.transaction_detail, name='transaction-detail'),
]
