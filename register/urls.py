from django.urls import path
from . import views

urlpatterns = [
    path("", views.register, name="register"),
    path("waiting-approval/", views.waiting_approval, name="waiting_approval"),
] 