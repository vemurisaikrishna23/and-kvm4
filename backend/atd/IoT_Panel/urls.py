# your_project/urls.py (or your_app/urls.py and include it)
from django.urls import path
from .views import *

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),

    path("dispenser-unit/add/", AddDispenserUnit.as_view(), name="add-dispenser-unit"),
]
