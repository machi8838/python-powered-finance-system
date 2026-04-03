"""
URL routes for the analytics app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.summary, name='summary'),
    path('monthly/', views.monthly_summary, name='summary-monthly'),
    path('recent/', views.recent_activity, name='summary-recent'),
    path('income/', views.income_total, name='summary-income'),
    path('expenses/', views.expense_total, name='summary-expenses'),
    path('balance/', views.balance, name='summary-balance'),
]
