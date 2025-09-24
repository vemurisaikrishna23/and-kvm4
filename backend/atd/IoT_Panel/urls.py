# your_project/urls.py (or your_app/urls.py and include it)
from django.urls import path
from .views import LoginView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
]
