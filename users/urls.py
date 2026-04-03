"""
URL routes for the users app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_list, name='user-list'),
    path('create/', views.user_create, name='user-create'),
    path('me/', views.me, name='user-me'),
    path('login/', views.login_view, name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    path('<int:user_id>/', views.user_detail, name='user-detail'),
]
