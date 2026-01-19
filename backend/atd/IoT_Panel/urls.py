# your_project/urls.py (or your_app/urls.py and include it)
from django.urls import path
from .views import *

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/validate-token-and-get-new-access-token/", ValidateTokenAndGetNewAccessToken.as_view(), name="validate-token-and-get-new-access-token"),
    path("customers/get/", GetCustomers.as_view(), name="get-customers"),
    
    path("dispenser-unit/add/", AddDispenserUnit.as_view(), name="add-dispenser-unit"),
    path("dispenser-unit/get/", GetDispenserUnits.as_view(), name="get-dispenser-units"),
    path("dispenser-unit/get-unassigned/", GetUnassignedDispenserUnits.as_view(), name="get-unassigned-dispenser-units"),
    path("dispenser-unit/edit/<int:id>/", EditDispenserUnit.as_view(), name="edit-dispenser-unit"),
    path("dispenser-unit/delete/<int:id>/", DeleteDispenserUnit.as_view(), name="delete-dispenser-unit"),

    path("gun-unit/add/", AddGunUnit.as_view(), name="add-gun-unit"),
    path("gun-unit/get/", GetGunUnits.as_view(), name="get-gun-units"),
    path("gun-unit/get-unassigned/", GetUnassignedGunUnits.as_view(), name="get-unassigned-gun-units"),
    path("gun-unit/edit/<int:id>/", EditGunUnit.as_view(), name="edit-gun-unit"),
    path("gun-unit/delete/<int:id>/", DeleteGunUnit.as_view(), name="delete-gun-unit"),

    path("node-unit/add/", AddNodeUnit.as_view(), name="add-node-unit"),
    path("node-unit/get/", GetNodeUnits.as_view(), name="get-node-units"),
    path("node-unit/get-unassigned/", GetUnassignedNodeUnits.as_view(), name="get-unassigned-node-units"),
    path("node-unit/edit/<int:id>/", EditNodeUnit.as_view(), name="edit-node-unit"),
    path("node-unit/delete/<int:id>/", DeleteNodeUnit.as_view(), name="delete-node-unit"),

    path("dispenser-gun-mapping-to-customer/add/", AddDispenserGunMappingToCustomer.as_view(), name="add-dispenser-gun-mapping-to-customer"),
    path("dispenser-gun-mapping-to-customer/get/", GetDispenserGunMappingToCustomer.as_view(), name="get-dispenser-gun-mapping-to-customer"),
    path("dispenser-gun-mapping-to-customer/get/<int:customer_id>/", GetDispenserGunMappingToCustomerByCustomerID.as_view(), name="get-dispenser-gun-mapping-to-customer-by-customer-id"),
    path("dispenser-gun-mapping-to-customer/get-by-delivery-location-ids/", GetDispenserGunMappingListByDeliveryLocationIDs.as_view(), name="get-dispenser-gun-mapping-to-customer-by-delivery-location-ids"),
    path("dispenser-gun-mapping-to-customer/edit/<int:id>/", EditDispenserGunMappingToCustomer.as_view(), name="edit-dispenser-gun-mapping-to-customer"),
    path("dispenser-gun-mapping-to-customer/edit-status/<int:id>/", EditStatusAndAssignedStatusOfDispenserGunMappingToCustomer.as_view(), name="edit-status-and-assigned-status-of-dispenser-gun-mapping-to-customer"),
    path("dispenser-gun-mapping-to-customer/delete/<int:id>/", DeleteDispenserGunMappingToCustomer.as_view(), name="delete-dispenser-gun-mapping-to-customer"),


    path("dispenser-gun-mapping-to-vehicle/add/", AddDispenserGunMappingToVehicles.as_view(), name="add-dispenser-gun-mapping-to-vehicles"),
    path("dispenser-gun-mapping-to-vehicle/get/", GetDispenserGunMappingToVehicles.as_view(), name="get-dispenser-gun-mapping-to-vehicles"),
    path("dispenser-gun-mapping-to-vehicle/get/<int:vehicle_id>/", GetDispenserGunMappingToVehiclesByVehicleID.as_view(), name="get-dispenser-gun-mapping-to-customer-by-vehicle-id"),
    path("dispenser-gun-mapping-to-vehicle/edit/<int:id>/", EditDispenserGunMappingToVehicles.as_view(), name="edit-dispenser-gun-mapping-to-vehicles"),
    path("dispenser-gun-mapping-to-vehicle/edit-status/<int:id>/", EditStatusAndAssignedStatusOfDispenserGunMappingToVehicles.as_view(), name="edit-status-and-assigned-status-of-dispenser-gun-mapping-to-vehicles"),
    path("dispenser-gun-mapping-to-vehicle/delete/<int:id>/", DeleteDispenserGunMappingToVehicles.as_view(), name="delete-dispenser-gun-mapping-to-vehicles"),


    path("node-dispenser-customer-mapping/add/", AssignNodeUnitAndDispenserGunMappingToCustomer.as_view(), name="assign-node-unit-and-dispenser-gun-mapping-to-customer"),
    path("node-dispenser-customer-mapping/get/", GetNodeDispenserCustomerMapping.as_view(), name="get-node-dispenser-customer-mapping"),
    path("node-dispenser-customer-mapping/get/<int:customer_id>/", GetNodeDispenserCustomerMappingByCustomerID.as_view(), name="get-node-dispenser-customer-mapping-by-customer-id"),
    path("node-dispenser-customer-mapping/edit/<int:id>/", EditNodeDispenserCustomerMapping.as_view(), name="edit-node-dispenser-customer-mapping"),
    path("node-dispenser-customer-mapping/edit-status/<int:id>/", EditStatusAndAssignedStatusOfNodeDispenserCustomerMapping.as_view(), name="edit-status-and-assigned-status-of-node-dispenser-customer-mapping"),
    path("node-dispenser-customer-mapping/delete/<int:id>/", DeleteNodeDispenserCustomerMapping.as_view(), name="delete-node-dispenser-customer-mapping"),

    path("delivery-location-mapping-dispenser-unit/add/", AddDeliveryLocationMappingDispenserUnit.as_view(), name="add-delivery-location-mapping-dispenser-unit"),
    path("delivery-location-mapping-dispenser-unit/get/", GetDeliveryLocationMappingDispenserUnit.as_view(), name="get-delivery-location-mapping-dispenser-unit"),
    path("delivery-location-mapping-dispenser-unit/get/<int:customer_id>/", GetDeliveryLocationMappingDispenserUnitByCustomerID.as_view(), name="get-delivery-location-mapping-dispenser-unit-by-customer-id"),
    path("delivery-location-mapping/dispenser-unit/by-poc/",GetDeliveryLocationMappingDispenserUnitByPOC.as_view(),name="get_delivery_location_mapping_dispenser_unit"),
    path("delivery-location-mapping-dispenser-unit/edit/<int:id>/", EditDeliveryLocationMappingDispenserUnit.as_view(), name="edit-delivery-location-mapping-dispenser-unit"),
    path("delivery-location-mapping-dispenser-unit/delete/<int:id>/", DeleteDeliveryLocationMappingDispenserUnit.as_view(), name="delete-delivery-location-mapping-dispenser-unit"),
    
    
    path("request-fuel-dispensing/create/", CreateRequestForFuelDispensing.as_view(), name="create-request-for-fuel-dispensing"),
    path("request-fuel-dispensing/get/", GetFuelDispensingRequests.as_view(), name="get-all-fuel-dispensing-requests"),
    path("request-fuel-dispensing/get/customer_id/<int:customer_id>/", GetFuelDispensingRequestsByCustomerID.as_view(), name="get-fuel-dispensing-requests-by-customer-id"),
    path("request-fuel-dispensing/get/dispenser_gun_mapping_id/<int:dispenser_gun_mapping_id>/", GetFuelDispensingRequestsByDispenserGunMappingID.as_view(), name="get-fuel-dispensing-requests-by-dispenser-gun-mapping-id"),
    path("request-fuel-dispensing/get/delivery_location_id/<int:delivery_location_id>/", GetFuelDispensingRequestsByDeliveryLocationID.as_view(), name="get-fuel-dispensing-requests-by-delivery-location-id"),
    path("request-fuel-dispensing/get/asset_id/<int:asset_id>/", GetFuelDispensingRequestsByAssetID.as_view(), name="get-fuel-dispensing-requests-by-asset-id"),
    path("request-fuel-dispensing/get/id/<int:id>/", GetFuelDispensingRequestsByID.as_view(), name="get-fuel-dispensing-requests-by-id"),
    path("request-fuel-dispensing/get/user_id/<int:user_id>/", GetFuelDispensingRequestsByUserID.as_view(), name="get-fuel-dispensing-requests-by-user-id"),


    path("vin-vehicle/add/", AddVINVehicle.as_view(), name="add_vin_vehicle"),
    path("vin-vehicle/get/<int:customer_id>/", GetVINVehicleByCustomerID.as_view(), name="vin-vehicle-get-by-customerid"),
    path("vin-vehicle/get/id/<int:vin_id>/", GetVINVehicleByID.as_view(), name="vin-vehicle-get-by-id"),
    path("vin-vehicle/get/vin/<str:vin>/", GetVINVehicleByVIN.as_view(), name="get_vin_vehicle_by_vin"),
    path("vin-vehicle/edit/<int:vin_id>/", EditVINVehicle.as_view(), name="edit-vin-vehicle"),
    path("vin-vehicle/delete/<int:vin_id>/", DeleteVINVehicle.as_view(), name="delete-vin-vehicle"),

    path("dashboard/consumption/<int:customer_id>/", ConsumptionPageDashBoardView.as_view(), name="consumption page"),
    path("dashboard/reconsiliance/<int:customer_id>/", DailyReconciliationDashBoardView.as_view(), name="reconsiliance page"),
    path("dashboard/overview/<int:customer_id>/", OverviewDashboard.as_view(), name="overview page"),


]


