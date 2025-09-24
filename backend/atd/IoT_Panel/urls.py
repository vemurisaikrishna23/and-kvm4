# your_project/urls.py (or your_app/urls.py and include it)
from django.urls import path
from .views import *

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),

    path("customers/get/", GetCustomers.as_view(), name="get-customers"),
    
    path("dispenser-unit/add/", AddDispenserUnit.as_view(), name="add-dispenser-unit"),
    path("dispenser-unit/get/", GetDispenserUnits.as_view(), name="get-dispenser-units"),
    path("dispenser-unit/edit/<int:id>/", EditDispenserUnit.as_view(), name="edit-dispenser-unit"),
    path("dispenser-unit/delete/<int:id>/", DeleteDispenserUnit.as_view(), name="delete-dispenser-unit"),

    path("gun-unit/add/", AddGunUnit.as_view(), name="add-gun-unit"),
]
