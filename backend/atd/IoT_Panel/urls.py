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
    path("gun-unit/get/", GetGunUnits.as_view(), name="get-gun-units"),
    path("gun-unit/edit/<int:id>/", EditGunUnit.as_view(), name="edit-gun-unit"),
    path("gun-unit/delete/<int:id>/", DeleteGunUnit.as_view(), name="delete-gun-unit"),

    path("node-unit/add/", AddNodeUnit.as_view(), name="add-node-unit"),
    path("node-unit/get/", GetNodeUnits.as_view(), name="get-node-units"),
]
