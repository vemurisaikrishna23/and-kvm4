"""
OpenAPI schema annotations for every IoT_Panel endpoint.
Applied via extend_schema_view() so views.py stays untouched.
Imported in apps.py ready() to register at startup.
"""
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiTypes, inline_serializer,
)
from drf_spectacular.types import OpenApiTypes as OT
from rest_framework import serializers as s


# ──────────────────────────────────────────────
#  AUTH
# ──────────────────────────────────────────────
def annotate_auth(views):
    extend_schema_view(
        post=extend_schema(
            summary="User Login",
            description="Authenticate a user with email and password. Returns JWT access and refresh tokens. Only users with IoT-related roles (IOT Admin, Accounts Admin, Dispenser Manager, Location Manager, Dispenser) are allowed.",
            examples=[
                OpenApiExample(
                    "Login Request",
                    value={"email": "user@company.com", "password": "SecurePass123"},
                    request_only=True,
                ),
                OpenApiExample(
                    "Login Success",
                    value={
                        "token": {"refresh": "eyJhbG...", "access": "eyJhbG..."},
                        "message": "Login Success",
                        "user_id": 5,
                        "name": "John Doe",
                        "email": "user@company.com",
                        "roles": ["IOT Admin"],
                    },
                    response_only=True,
                ),
            ],
        ),
    )(views.LoginView)

    extend_schema_view(
        post=extend_schema(
            summary="Validate Token & Get New Access Token",
            description="Submit a personal_access_token (from the existing system) to receive a new JWT access/refresh token pair. The token is verified against the personal_access_tokens table.",
            examples=[
                OpenApiExample(
                    "Token Validation Request",
                    value={"personal_access_token": "abc123xyz"},
                    request_only=True,
                ),
            ],
        ),
    )(views.ValidateTokenAndGetNewAccessToken)


# ──────────────────────────────────────────────
#  CUSTOMERS
# ──────────────────────────────────────────────
def annotate_customers(views):
    extend_schema_view(
        get=extend_schema(
            summary="Get All Customers",
            description="Retrieve all customers. Restricted to IOT Admin role.",
        ),
    )(views.GetCustomers)


# ──────────────────────────────────────────────
#  DISPENSER UNITS
# ──────────────────────────────────────────────
def annotate_dispenser_units(views):
    extend_schema_view(
        post=extend_schema(
            summary="Add Dispenser Unit",
            description="Register a new dispenser hardware unit. All fields are mandatory except remarks.",
            examples=[
                OpenApiExample(
                    "Add Dispenser",
                    value={
                        "serial_number": "DSP-001",
                        "batch_number": "BATCH-2024-01",
                        "imei_number": "862298050423811",
                        "mac_address": "00:1A:2B:3C:4D:5E",
                        "firmware_version": "2.1.5",
                        "hardware_version": "1.0",
                        "production_date": "2024-01-15",
                        "remarks": "Primary unit",
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.AddDispenserUnit)

    extend_schema_view(
        get=extend_schema(
            summary="Get All Dispenser Units",
            description="Retrieve every registered dispenser unit, including assigned and unassigned.",
        ),
    )(views.GetDispenserUnits)

    extend_schema_view(
        get=extend_schema(
            summary="Get Unassigned Dispenser Units",
            description="Retrieve dispenser units whose assigned_status is False — available for mapping.",
        ),
    )(views.GetUnassignedDispenserUnits)

    extend_schema_view(
        post=extend_schema(
            summary="Edit Dispenser Unit",
            description="Update an existing dispenser unit by its ID.",
        ),
    )(views.EditDispenserUnit)

    extend_schema_view(
        delete=extend_schema(
            summary="Delete Dispenser Unit",
            description="Delete a dispenser unit by its ID. Fails if the unit is still mapped to a customer or vehicle.",
        ),
    )(views.DeleteDispenserUnit)


# ──────────────────────────────────────────────
#  GUN UNITS
# ──────────────────────────────────────────────
def annotate_gun_units(views):
    extend_schema_view(
        post=extend_schema(
            summary="Add Gun Unit",
            description="Register a new gun unit (RFID reader + nozzle hardware). All fields mandatory except battery_capacity, backup_hours, and remarks.",
            examples=[
                OpenApiExample(
                    "Add Gun Unit",
                    value={
                        "serial_number": "GUN-001",
                        "mac_address": "AA:BB:CC:DD:EE:FF",
                        "firmware_version": "1.0.0",
                        "hardware_version": "1.0",
                        "rfid_reader_type": "RFID-UHF",
                        "batch_number": "BATCH-GUN-01",
                        "production_date": "2024-02-10",
                        "battery_capacity": 5000,
                        "backup_hours": 48,
                        "remarks": "",
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.AddGunUnit)

    extend_schema_view(get=extend_schema(summary="Get All Gun Units", description="Retrieve every registered gun unit."))(views.GetGunUnits)
    extend_schema_view(get=extend_schema(summary="Get Unassigned Gun Units", description="Retrieve gun units whose assigned_status is False — available for mapping."))(views.GetUnassignedGunUnits)
    extend_schema_view(post=extend_schema(summary="Edit Gun Unit", description="Update an existing gun unit by its ID."))(views.EditGunUnit)
    extend_schema_view(delete=extend_schema(summary="Delete Gun Unit", description="Delete a gun unit by its ID."))(views.DeleteGunUnit)


# ──────────────────────────────────────────────
#  NODE UNITS
# ──────────────────────────────────────────────
def annotate_node_units(views):
    extend_schema_view(
        post=extend_schema(
            summary="Add Node Unit",
            description="Register a new node unit (IoT gateway device).",
            examples=[
                OpenApiExample(
                    "Add Node Unit",
                    value={
                        "serial_number": "NODE-001",
                        "imei_number": "860011050423811",
                        "mac_address": "11:22:33:44:55:66",
                        "firmware_version": "1.2.0",
                        "hardware_version": "2.0",
                        "batch_number": "BATCH-NODE-01",
                        "production_date": "2024-03-01",
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.AddNodeUnit)

    extend_schema_view(get=extend_schema(summary="Get All Node Units", description="Retrieve every registered node unit."))(views.GetNodeUnits)
    extend_schema_view(get=extend_schema(summary="Get Unassigned Node Units", description="Retrieve node units whose assigned_status is False."))(views.GetUnassignedNodeUnits)
    extend_schema_view(post=extend_schema(summary="Edit Node Unit", description="Update an existing node unit by its ID."))(views.EditNodeUnit)
    extend_schema_view(delete=extend_schema(summary="Delete Node Unit", description="Delete a node unit by its ID."))(views.DeleteNodeUnit)


# ──────────────────────────────────────────────
#  DISPENSER-GUN MAPPING → CUSTOMER
# ──────────────────────────────────────────────
def annotate_dgm_customer(views):
    extend_schema_view(
        post=extend_schema(
            summary="Map Dispenser-Gun to Customer",
            description=(
                "Assign a dispenser unit (and optionally a gun unit) to a customer. "
                "Includes totalizer readings, fuel grade, nozzle number, and optional fuel-level sensor config."
            ),
            examples=[
                OpenApiExample(
                    "Create Mapping",
                    value={
                        "customer": 3,
                        "dispenser_unit": 1,
                        "gun_unit": 2,
                        "totalizer_reading": 12345.67,
                        "total_reading_amount": 500000.00,
                        "live_price": 95.50,
                        "grade": 1,
                        "nozzle": 1,
                        "fuel_level_sensor": False,
                        "tank_capacity": 5000.0,
                        "remarks": "Site A installation",
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.AddDispenserGunMappingToCustomer)

    extend_schema_view(get=extend_schema(summary="Get All Dispenser-Gun-Customer Mappings", description="Retrieve all active dispenser-gun-to-customer mappings."))(views.GetDispenserGunMappingToCustomer)
    extend_schema_view(get=extend_schema(summary="Get Mappings by Customer ID", description="Retrieve all dispenser-gun mappings for a specific customer."))(views.GetDispenserGunMappingToCustomerByCustomerID)
    extend_schema_view(
        post=extend_schema(
            summary="Get Mappings by Delivery Location IDs",
            description="Retrieve dispenser-gun-customer mappings matching a list of delivery location IDs.",
            examples=[
                OpenApiExample("Request", value={"delivery_location_ids": [1, 2, 5]}, request_only=True),
            ],
        ),
    )(views.GetDispenserGunMappingListByDeliveryLocationIDs)
    extend_schema_view(post=extend_schema(summary="Edit Mapping", description="Update a dispenser-gun-customer mapping by its ID."))(views.EditDispenserGunMappingToCustomer)
    extend_schema_view(post=extend_schema(summary="Edit Status of Mapping", description="Toggle status and/or assigned_status of a dispenser-gun-customer mapping."))(views.EditStatusAndAssignedStatusOfDispenserGunMappingToCustomer)
    extend_schema_view(delete=extend_schema(summary="Delete Mapping", description="Remove a dispenser-gun-customer mapping by its ID."))(views.DeleteDispenserGunMappingToCustomer)


# ──────────────────────────────────────────────
#  DISPENSER-GUN MAPPING → VEHICLE
# ──────────────────────────────────────────────
def annotate_dgm_vehicle(views):
    extend_schema_view(
        post=extend_schema(
            summary="Map Dispenser-Gun to Vehicle",
            description=(
                "Assign a dispenser unit (and optionally a gun unit) to a vehicle. "
                "**Restricted to IOT Admin role.**\n\n"
                "## Required fields\n"
                "| Field | Type | Description |\n"
                "|---|---|---|\n"
                "| `vehicle` | int | Primary key of the vehicle (from Vehicles table). Validated for existence. |\n"
                "| `dispenser_unit` | int | Primary key of the dispenser unit. **Must not be already assigned** (`assigned_status=False`). |\n"
                "| `totalizer_reading` | float | Current totalizer volume reading at the time of assignment (litres). |\n"
                "| `total_reading_amount` | float | Current totalizer amount reading at the time of assignment (currency). |\n"
                "| `live_price` | float | Current fuel price per litre/unit. |\n"
                "| `grade` | int | Fuel grade/type index (e.g. 1=Diesel, 2=Petrol). |\n"
                "| `nozzle` | int | Nozzle number on the dispenser. |\n"
                "| `dispenser_position` | int | Physical position/slot of the dispenser on the vehicle. |\n\n"
                "## Optional fields\n"
                "| Field | Type | Description |\n"
                "|---|---|---|\n"
                "| `gun_unit` | int or null | Primary key of the gun unit. Must not be already assigned. |\n"
                "| `installation_mode` | int | 0=Static, 1=Mobility. Defaults to model default. |\n"
                "| `fuel_level_sensor` | bool | Whether a fuel-level sensor is installed. Default `false`. |\n"
                "| `fuel_level_sensor_type` | int or null | Sensor type (0=None, 1=Capacitive). Required if `fuel_level_sensor=true`. |\n"
                "| `fuel_level_sensor_brand` | string | Sensor brand name. |\n"
                "| `fuel_level_sensor_description` | string | Sensor description. |\n"
                "| `fuel_level_sensor_configuration` | JSON | Sensor calibration/config data. |\n"
                "| `tank_capacity` | float or null | Tank capacity in litres. |\n"
                "| `obd_sensor` | bool | Whether an OBD (odometer) sensor is connected. Default `false`. |\n"
                "| `odometer_reading` | int or null | Current odometer reading. Required if `obd_sensor=true`. |\n"
                "| `odometer_mac_id` | string | Bluetooth MAC address of the OBD device. Required if `obd_sensor=true`. |\n"
                "| `remarks` | string | Free-text notes. |\n\n"
                "## Validation rules\n"
                "- The dispenser unit must have `assigned_status=False` (not already assigned to another customer/vehicle).\n"
                "- The gun unit (if provided) must also have `assigned_status=False`.\n"
                "- If any fuel sensor detail field is provided, `fuel_level_sensor` must be `true`.\n"
                "- If any odometer field is provided, `obd_sensor` must be `true`.\n"
                "- On success, both the dispenser unit and gun unit are marked as `assigned_status=True`.\n\n"
                "## Responses\n"
                "- **201**: Mapping created successfully.\n"
                "- **400**: Validation error (unit already assigned, missing required field, etc.).\n"
                "- **403**: User does not have IOT Admin role."
            ),
            examples=[
                OpenApiExample(
                    "Minimal (required fields only)",
                    description="Assign dispenser #1 to vehicle #10 with no gun unit, no sensors",
                    value={
                        "vehicle": 10,
                        "dispenser_unit": 1,
                        "totalizer_reading": 5000.00,
                        "total_reading_amount": 200000.00,
                        "live_price": 95.50,
                        "grade": 1,
                        "nozzle": 1,
                        "dispenser_position": 1,
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "With gun unit + fuel sensor",
                    description="Full setup with gun unit and capacitive fuel level sensor",
                    value={
                        "vehicle": 10,
                        "dispenser_unit": 1,
                        "gun_unit": 2,
                        "totalizer_reading": 5000.00,
                        "total_reading_amount": 200000.00,
                        "live_price": 95.50,
                        "grade": 1,
                        "nozzle": 1,
                        "dispenser_position": 1,
                        "installation_mode": 1,
                        "fuel_level_sensor": True,
                        "fuel_level_sensor_type": 1,
                        "fuel_level_sensor_brand": "Omntec",
                        "fuel_level_sensor_description": "Capacitive probe for diesel",
                        "fuel_level_sensor_configuration": {"length_mm": 1200, "offset_mm": 50},
                        "tank_capacity": 3000.0,
                        "remarks": "Tanker truck A — main tank",
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "With OBD sensor",
                    description="Setup with OBD odometer sensor connected via Bluetooth",
                    value={
                        "vehicle": 10,
                        "dispenser_unit": 1,
                        "totalizer_reading": 5000.00,
                        "total_reading_amount": 200000.00,
                        "live_price": 95.50,
                        "grade": 1,
                        "nozzle": 1,
                        "dispenser_position": 1,
                        "obd_sensor": True,
                        "odometer_reading": 45230,
                        "odometer_mac_id": "AA:BB:CC:DD:EE:01",
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "Success Response",
                    value={"message": "Dispenser & Gun Unit Mapping to Vehicles Created Successfully"},
                    response_only=True,
                    status_codes=["201"],
                ),
                OpenApiExample(
                    "Error — Dispenser already assigned",
                    value={"error": "This dispenser unit is already assigned and cannot be allotted."},
                    response_only=True,
                    status_codes=["400"],
                ),
                OpenApiExample(
                    "Error — Not authorized",
                    value={"error": "You are not authorized to add a dispenser gun mapping to vehicles"},
                    response_only=True,
                    status_codes=["403"],
                ),
            ],
        ),
    )(views.AddDispenserGunMappingToVehicles)

    extend_schema_view(get=extend_schema(summary="Get All Vehicle Mappings", description="Retrieve all dispenser-gun-to-vehicle mappings."))(views.GetDispenserGunMappingToVehicles)
    extend_schema_view(get=extend_schema(summary="Get Vehicle Mapping by ID", description="Retrieve a specific vehicle mapping by its primary key."))(views.GetDispenserGunMappingToVehiclesByID)
    extend_schema_view(get=extend_schema(summary="Get Vehicle Mappings by Vehicle ID", description="Retrieve all active dispenser-gun mappings for a specific vehicle."))(views.GetDispenserGunMappingToVehiclesByVehicleID)
    extend_schema_view(
        post=extend_schema(
            summary="Get Vehicle Mapping by Vehicle Number",
            description="Look up dispenser-gun mappings using the vehicle's registration number.",
            examples=[OpenApiExample("Request", value={"vehicle_no": "AP30BA4611"}, request_only=True)],
        ),
    )(views.GetDispenserGunMappingByVehicleNo)
    extend_schema_view(post=extend_schema(summary="Edit Vehicle Mapping", description="Update a vehicle mapping by its ID."))(views.EditDispenserGunMappingToVehicles)
    extend_schema_view(post=extend_schema(summary="Edit Status of Vehicle Mapping", description="Toggle status and/or assigned_status of a vehicle mapping."))(views.EditStatusAndAssignedStatusOfDispenserGunMappingToVehicles)
    extend_schema_view(delete=extend_schema(summary="Delete Vehicle Mapping", description="Remove a vehicle mapping by its ID."))(views.DeleteDispenserGunMappingToVehicles)


# ──────────────────────────────────────────────
#  NODE-DISPENSER-CUSTOMER MAPPING
# ──────────────────────────────────────────────
def annotate_ndc_mapping(views):
    extend_schema_view(
        post=extend_schema(
            summary="Assign Node + Dispenser to Customer",
            description="Create a node-dispenser-customer mapping. Links a node unit (IoT gateway) and optionally a dispenser unit to a customer.",
            examples=[
                OpenApiExample(
                    "Assign",
                    value={"node_unit": 1, "dispenser_unit": 2, "customer": 3, "fuel_sensor_type": 0, "remarks": "Ultrasonic sensor setup"},
                    request_only=True,
                ),
            ],
        ),
    )(views.AssignNodeUnitAndDispenserGunMappingToCustomer)

    extend_schema_view(get=extend_schema(summary="Get All Node-Dispenser-Customer Mappings", description="Retrieve all mappings."))(views.GetNodeDispenserCustomerMapping)
    extend_schema_view(get=extend_schema(summary="Get by Customer ID", description="Retrieve node-dispenser mappings for a specific customer."))(views.GetNodeDispenserCustomerMappingByCustomerID)
    extend_schema_view(post=extend_schema(summary="Edit Mapping", description="Update a node-dispenser-customer mapping by ID."))(views.EditNodeDispenserCustomerMapping)
    extend_schema_view(post=extend_schema(summary="Edit Status", description="Toggle status/assigned_status of a node-dispenser-customer mapping."))(views.EditStatusAndAssignedStatusOfNodeDispenserCustomerMapping)
    extend_schema_view(delete=extend_schema(summary="Delete Mapping", description="Remove a node-dispenser-customer mapping by ID."))(views.DeleteNodeDispenserCustomerMapping)


# ──────────────────────────────────────────────
#  DELIVERY LOCATION MAPPING
# ──────────────────────────────────────────────
def annotate_dl_mapping(views):
    extend_schema_view(
        post=extend_schema(
            summary="Map Delivery Location to Dispenser",
            description=(
                "Link a delivery location to a dispenser-gun-customer mapping. "
                "Optionally specify DU_Accessible_delivery_locations — a list of other delivery location IDs that can also access this dispenser."
            ),
            examples=[
                OpenApiExample(
                    "Create DL Mapping",
                    value={
                        "delivery_location_id": 10,
                        "dispenser_gun_mapping_id": 5,
                        "DU_Accessible_delivery_locations": [11, 12],
                        "remarks": "Main gate installation",
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.AddDeliveryLocationMappingDispenserUnit)

    extend_schema_view(get=extend_schema(summary="Get All DL Mappings", description="Retrieve all delivery-location-to-dispenser mappings."))(views.GetDeliveryLocationMappingDispenserUnit)
    extend_schema_view(get=extend_schema(summary="Get DL Mappings by Customer ID", description="Retrieve delivery-location mappings for a specific customer's locations."))(views.GetDeliveryLocationMappingDispenserUnitByCustomerID)
    extend_schema_view(get=extend_schema(summary="Get DL Mappings by POC (Logged-in User)", description="Retrieve delivery-location mappings accessible to the authenticated user based on their Point of Contact assignments."))(views.GetDeliveryLocationMappingDispenserUnitByPOC)
    extend_schema_view(post=extend_schema(summary="Edit DL Mapping", description="Update a delivery-location-dispenser mapping by ID."))(views.EditDeliveryLocationMappingDispenserUnit)
    extend_schema_view(delete=extend_schema(summary="Delete DL Mapping", description="Remove a delivery-location-dispenser mapping by ID."))(views.DeleteDeliveryLocationMappingDispenserUnit)


# ──────────────────────────────────────────────
#  FUEL DISPENSING REQUESTS
# ──────────────────────────────────────────────
def annotate_fuel_dispensing(views):
    extend_schema_view(
        post=extend_schema(
            summary="Create Fuel Dispensing Request",
            description=(
                "Create a new fuel dispensing transaction. Supports three request types:\n\n"
                "- **request_type=0 (Volume)**: dispenser_volume is required (litres). dispenser_price must be omitted.\n"
                "- **request_type=1 (Amount)**: dispenser_price is required (currency). dispenser_volume must be omitted.\n"
                "- **request_type=2 (Full Tank Mode)**: Neither volume nor price is required — the dispenser runs until the tank is full.\n\n"
                "Supports two vehicle modes:\n"
                "- **request_vehicle=0 (Asset)**: Provide asset_id (integer) and delivery_location_id.\n"
                "- **request_vehicle=1 (VIN)**: Provide asset_id (VIN string). Delivery location is resolved from the VIN record. "
                "Only request_type=0 (Volume) is allowed for VIN requests.\n\n"
                "Returns the created transaction details including the generated transaction_id."
            ),
            examples=[
                OpenApiExample(
                    "Volume Request (Asset)",
                    description="Dispense 50.5 litres to asset #42 at delivery location #10",
                    value={
                        "user_id": 5,
                        "customer_id": 3,
                        "delivery_location_id": 10,
                        "asset_id": "42",
                        "request_vehicle": 0,
                        "request_type": 0,
                        "dispenser_volume": 50.5,
                        "remarks": "Routine refuel",
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "Amount Request (Asset)",
                    description="Dispense fuel worth 2000 currency units",
                    value={
                        "user_id": 5,
                        "customer_id": 3,
                        "delivery_location_id": 10,
                        "asset_id": "42",
                        "request_vehicle": 0,
                        "request_type": 1,
                        "dispenser_price": 2000.0,
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "Full Tank Mode (Asset)",
                    description="Dispense until tank is full — no volume or price preset",
                    value={
                        "user_id": 5,
                        "customer_id": 3,
                        "delivery_location_id": 10,
                        "asset_id": "42",
                        "request_vehicle": 0,
                        "request_type": 2,
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "VIN Request (Volume only)",
                    description="VIN-based request — delivery location auto-resolved from VIN record",
                    value={
                        "user_id": 5,
                        "customer_id": 3,
                        "asset_id": "WVWZZZ3CZ3E012345",
                        "request_vehicle": 1,
                        "request_type": 0,
                        "dispenser_volume": 60.0,
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.CreateRequestForFuelDispensing)

    extend_schema_view(get=extend_schema(summary="Get All Fuel Dispensing Requests", description="Retrieve every fuel dispensing request. Restricted by user role — IOT Admin sees all, Accounts Admin sees only their customer's requests."))(views.GetFuelDispensingRequests)

    extend_schema_view(
        get=extend_schema(
            summary="Get Requests by Customer ID",
            description="Retrieve fuel dispensing requests for a specific customer. Supports optional date-range filtering via query parameters.",
            parameters=[
                OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY, required=False, description="Filter from this date (YYYY-MM-DD)"),
                OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY, required=False, description="Filter until this date (YYYY-MM-DD)"),
            ],
        ),
    )(views.GetFuelDispensingRequestsByCustomerID)

    extend_schema_view(get=extend_schema(summary="Get Requests by Dispenser-Gun Mapping ID", description="Retrieve all fuel dispensing requests linked to a specific dispenser-gun-customer mapping."))(views.GetFuelDispensingRequestsByDispenserGunMappingID)
    extend_schema_view(get=extend_schema(summary="Get Requests by Delivery Location ID", description="Retrieve all fuel dispensing requests for a specific delivery location."))(views.GetFuelDispensingRequestsByDeliveryLocationID)
    extend_schema_view(get=extend_schema(summary="Get Requests by Asset ID", description="Retrieve fuel dispensing requests for a specific asset (vehicle/equipment)."))(views.GetFuelDispensingRequestsByAssetID)
    extend_schema_view(get=extend_schema(summary="Get Request by ID", description="Retrieve a single fuel dispensing request with full transaction log details."))(views.GetFuelDispensingRequestsByID)
    extend_schema_view(get=extend_schema(summary="Get Requests by User ID", description="Retrieve all fuel dispensing requests created by a specific user."))(views.GetFuelDispensingRequestsByUserID)


# ──────────────────────────────────────────────
#  VIN VEHICLES
# ──────────────────────────────────────────────
def annotate_vin(views):
    extend_schema_view(
        post=extend_schema(
            summary="Add VIN Vehicle",
            description=(
                "Register a new VIN (Vehicle Identification Number) record. VINs are one-time-use "
                "fuel dispensing vouchers tied to a customer, delivery location(s), and point-of-contact user(s). "
                "The dispense_volume field sets the maximum litres allowed for this VIN."
            ),
            examples=[
                OpenApiExample(
                    "Add VIN",
                    value={
                        "vin": "WVWZZZ3CZ3E012345",
                        "customer_id": 2,
                        "delivery_location_id": [1, 2],
                        "point_of_contact_id": [4, 5],
                        "vehicle_type": 1,
                        "capacity": 100.0,
                        "dispense_volume": 60.0,
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.AddVINVehicle)

    extend_schema_view(get=extend_schema(
        summary="Get VIN Vehicles by Customer ID",
        description="Retrieve VIN vehicles for a customer. Supports ?used=true/false query param to filter by usage status.",
        parameters=[OpenApiParameter(name="used", type=bool, location=OpenApiParameter.QUERY, required=False, description="Filter by usage status: true=used, false=unused")],
    ))(views.GetVINVehicleByCustomerID)

    extend_schema_view(get=extend_schema(summary="Get VIN Vehicle by ID", description="Retrieve a single VIN vehicle record by its database ID."))(views.GetVINVehicleByID)
    extend_schema_view(get=extend_schema(summary="Get VIN Vehicle by VIN String", description="Retrieve a VIN vehicle record by the actual VIN string."))(views.GetVINVehicleByVIN)

    extend_schema_view(
        put=extend_schema(
            summary="Edit VIN Vehicle",
            description="Update a VIN vehicle record. Only the provided fields are updated.",
            examples=[
                OpenApiExample(
                    "Edit VIN",
                    value={"delivery_location_id": [1, 2, 3], "capacity": 120.0},
                    request_only=True,
                ),
            ],
        ),
    )(views.EditVINVehicle)

    extend_schema_view(delete=extend_schema(summary="Delete VIN Vehicle", description="Delete a VIN vehicle record by its ID."))(views.DeleteVINVehicle)


# ──────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────
def annotate_dashboard(views):
    common_params = [
        OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY, required=False, description="Start date (YYYY-MM-DD)"),
        OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY, required=False, description="End date (YYYY-MM-DD)"),
    ]

    extend_schema_view(
        get=extend_schema(
            summary="Consumption Dashboard",
            description="Returns top 10 consuming assets and top 10 consuming users for a customer, within an optional date range. Aggregates by dispenser_received_volume.",
            parameters=common_params,
        ),
    )(views.ConsumptionPageDashBoardView)

    extend_schema_view(
        get=extend_schema(
            summary="Daily Reconciliation Dashboard",
            description="Returns per-dispenser daily reconciliation data for a customer. Requires start_date and end_date. Shows totalizer readings, dispensed volume, and validation status.",
            parameters=common_params,
        ),
    )(views.DailyReconciliationDashBoardView)

    extend_schema_view(
        get=extend_schema(
            summary="Overview Dashboard",
            description="Returns summary metrics for a customer: total transactions, total volume dispensed, total assets fueled, and per-dispenser consumption breakdown.",
            parameters=common_params,
        ),
    )(views.OverviewDashboard)


# ──────────────────────────────────────────────
#  ORDER FUEL DISPENSING
# ──────────────────────────────────────────────
def annotate_order_dispensing(views):
    extend_schema_view(
        post=extend_schema(
            summary="Create Order Fuel Dispensing Request",
            description=(
                "Create a fuel dispensing transaction linked to an order/route plan. Validates against remaining order quantity.\n\n"
                "- **request_type=0 (Volume)**: dispenser_volume required. Checked against remaining order quantity.\n"
                "- **request_type=1 (Amount)**: dispenser_price required.\n"
                "- **request_type=2 (Full Tank)**: No preset needed — device dispenses until full.\n\n"
                "The asset can be provided by ID (existing asset) or by name (ad-hoc asset for the trip)."
            ),
            examples=[
                OpenApiExample(
                    "Order Volume Request",
                    value={
                        "user_id": 5,
                        "route_plan_details_id": 12,
                        "dispenser_gun_mapping_id": 3,
                        "asset_id": "42",
                        "request_type": 0,
                        "dispenser_volume": 100.0,
                        "remarks": "Order delivery refuel",
                    },
                    request_only=True,
                ),
                OpenApiExample(
                    "Order Full Tank Request",
                    value={
                        "user_id": 5,
                        "route_plan_details_id": 12,
                        "dispenser_gun_mapping_id": 3,
                        "asset_name": "TN01AB1234",
                        "request_type": 2,
                    },
                    request_only=True,
                ),
            ],
        ),
    )(views.CreateOrderRequestForFuelDispensing)

    extend_schema_view(get=extend_schema(summary="Get All Order Dispensing Requests", description="Retrieve every order-based fuel dispensing request."))(views.GetOrderFuelDispensingRequests)
    extend_schema_view(get=extend_schema(summary="Get Order Request by ID", description="Retrieve a single order dispensing request with full transaction log."))(views.GetOrderFuelDispensingRequestsById)
    extend_schema_view(get=extend_schema(summary="Get by Vehicle ID", description="Retrieve order dispensing requests for a specific vehicle."))(views.GetOrderFuelDispensingRequestsByVehicleId)
    extend_schema_view(get=extend_schema(summary="Get by Driver ID", description="Retrieve order dispensing requests created by a specific driver."))(views.GetOrderFuelDispensingRequestsByDriverId)
    extend_schema_view(get=extend_schema(summary="Get by Customer ID", description="Retrieve order dispensing requests for a specific customer."))(views.GetOrderFuelDispensingRequestsByCustomerId)
    extend_schema_view(get=extend_schema(summary="Get by Route Plan ID", description="Retrieve order dispensing requests for a specific route plan."))(views.GetOrderFuelDispensingRequestsByRoutePlanId)
    extend_schema_view(get=extend_schema(summary="Get by Route Plan Details ID", description="Retrieve order dispensing requests for a specific route plan detail entry."))(views.GetOrderFuelDispensingRequestsByRoutePlanDetailsId)
    extend_schema_view(get=extend_schema(summary="Get by Order ID", description="Retrieve order dispensing requests for a specific order."))(views.GetOrderFuelDispensingRequestsByOrderId)


# ──────────────────────────────────────────────
#  FUEL READINGS
# ──────────────────────────────────────────────
def annotate_fuel_readings(views):
    common_params = [
        OpenApiParameter(name="start_epoch", type=int, location=OpenApiParameter.QUERY, required=False, description="Start epoch timestamp (seconds)"),
        OpenApiParameter(name="end_epoch", type=int, location=OpenApiParameter.QUERY, required=False, description="End epoch timestamp (seconds)"),
        OpenApiParameter(name="type", type=int, location=OpenApiParameter.QUERY, required=False, description="Reading type filter (msg_type value)"),
    ]

    extend_schema_view(
        get=extend_schema(
            summary="Get Fuel Readings by Customer Mapping ID",
            description="Retrieve fuel sensor reading logs for a dispenser-gun-customer mapping. Supports epoch-based date range and type filtering.",
            parameters=common_params,
        ),
    )(views.GetFuelReadingsLogsWithDispenserGunMappingCustomerID)

    extend_schema_view(
        get=extend_schema(
            summary="Get Fuel Readings by Vehicle Mapping ID",
            description="Retrieve fuel sensor reading logs for a dispenser-gun-vehicle mapping. Supports epoch-based date range and type filtering.",
            parameters=common_params,
        ),
    )(views.GetFuelReadingsLogsWithDispenserGunMappingVehicleID)


# ──────────────────────────────────────────────
#  HELPER: Bind request serializer to POST/PUT/PATCH views that drf-spectacular
#  can't auto-detect (plain APIViews without serializer_class).
# ──────────────────────────────────────────────
VIEW_SERIALIZER_MAPPING = {
    'LoginView': ('post', 'LoginSerializer'),
    'AddDispenserUnit': ('post', 'CreateDispenserUnitSerializer'),
    'EditDispenserUnit': ('post', 'EditDispenserUnitSerializer'),
    'AddGunUnit': ('post', 'CreateGunUnitSerializer'),
    'EditGunUnit': ('post', 'EditGunUnitSerializer'),
    'AddNodeUnit': ('post', 'CreateNodeUnitSerializer'),
    'EditNodeUnit': ('post', 'EditNodeUnitSerializer'),
    'AddDispenserGunMappingToCustomer': ('post', 'CreateDispenserGunMappingToCustomerSerializer'),
    'EditDispenserGunMappingToCustomer': ('post', 'EditDispenserGunMappingToCustomerSerializer'),
    'EditStatusAndAssignedStatusOfDispenserGunMappingToCustomer': ('post', 'EditStatusAndAssignedStatusOfDispenserGunMappingToCustomerSerializer'),
    'AddDispenserGunMappingToVehicles': ('post', 'CreateDispenserGunMappingToVehiclesSerializer'),
    'EditDispenserGunMappingToVehicles': ('post', 'EditDispenserGunMappingToVehiclesSerializer'),
    'EditStatusAndAssignedStatusOfDispenserGunMappingToVehicles': ('post', 'EditStatusAndAssignedStatusOfDispenserGunMappingToVehiclesSerializer'),
    'AssignNodeUnitAndDispenserGunMappingToCustomer': ('post', 'AssignNodeUnitAndDispenserGunMappingToCustomerSerializer'),
    'EditNodeDispenserCustomerMapping': ('post', 'EditNodeDispenserCustomerMappingSerializer'),
    'EditStatusAndAssignedStatusOfNodeDispenserCustomerMapping': ('post', 'EditStatusAndAssignedStatusOfNodeDispenserCustomerMappingSerializer'),
    'AddDeliveryLocationMappingDispenserUnit': ('post', 'AddDeliveryLocationMappingDispenserUnitSerializer'),
    'EditDeliveryLocationMappingDispenserUnit': ('post', 'EditDeliveryLocationMappingDispenserUnitSerializer'),
    'GetDispenserGunMappingListByDeliveryLocationIDs': ('post', 'GetDispenserGunMappingListByDeliveryLocationIDsSerializer'),
    'CreateRequestForFuelDispensing': ('post', 'CreateRequestForFuelDispensingSerializer'),
    'AddVINVehicle': ('post', 'AddVINVehicleSerializer'),
    'EditVINVehicle': ('put', 'EditVINVehicleSerializer'),
    'CreateOrderRequestForFuelDispensing': ('post', 'CreateRequestForOrderFuelDispensingSerializer'),
    'GetDispenserGunMappingByVehicleNo': ('post', 'VehicleNoSerializer'),
}


def _bind_request_serializers(views, serializer_map):
    """For each view listed in VIEW_SERIALIZER_MAPPING, apply an extend_schema
    with request= pointing to the real serializer so the request body + examples
    appear in the generated schema."""
    for view_name, (method, ser_name) in VIEW_SERIALIZER_MAPPING.items():
        view_cls = getattr(views, view_name, None)
        ser_cls = serializer_map.get(ser_name)
        if view_cls is None or ser_cls is None:
            continue
        handler = getattr(view_cls, method, None)
        if handler is None:
            continue
        decorated = extend_schema(request=ser_cls)(handler)
        setattr(view_cls, method, decorated)


# ──────────────────────────────────────────────
#  MASTER ENTRY POINT — called from apps.py ready()
# ──────────────────────────────────────────────
def apply_all_annotations():
    from IoT_Panel import views
    from IoT_Panel.serializers import (
        LoginSerializer,
        CreateDispenserUnitSerializer, EditDispenserUnitSerializer,
        CreateGunUnitSerializer, EditGunUnitSerializer,
        CreateNodeUnitSerializer, EditNodeUnitSerializer,
        CreateDispenserGunMappingToCustomerSerializer, EditDispenserGunMappingToCustomerSerializer,
        EditStatusAndAssignedStatusOfDispenserGunMappingToCustomerSerializer,
        CreateDispenserGunMappingToVehiclesSerializer, EditDispenserGunMappingToVehiclesSerializer,
        EditStatusAndAssignedStatusOfDispenserGunMappingToVehiclesSerializer,
        AssignNodeUnitAndDispenserGunMappingToCustomerSerializer,
        EditNodeDispenserCustomerMappingSerializer,
        EditStatusAndAssignedStatusOfNodeDispenserCustomerMappingSerializer,
        AddDeliveryLocationMappingDispenserUnitSerializer, EditDeliveryLocationMappingDispenserUnitSerializer,
        GetDispenserGunMappingListByDeliveryLocationIDsSerializer,
        CreateRequestForFuelDispensingSerializer,
        AddVINVehicleSerializer, EditVINVehicleSerializer,
        CreateRequestForOrderFuelDispensingSerializer,
        VehicleNoSerializer,
    )
    _serializer_map = {
        'LoginSerializer': LoginSerializer,
        'CreateDispenserUnitSerializer': CreateDispenserUnitSerializer,
        'EditDispenserUnitSerializer': EditDispenserUnitSerializer,
        'CreateGunUnitSerializer': CreateGunUnitSerializer,
        'EditGunUnitSerializer': EditGunUnitSerializer,
        'CreateNodeUnitSerializer': CreateNodeUnitSerializer,
        'EditNodeUnitSerializer': EditNodeUnitSerializer,
        'CreateDispenserGunMappingToCustomerSerializer': CreateDispenserGunMappingToCustomerSerializer,
        'EditDispenserGunMappingToCustomerSerializer': EditDispenserGunMappingToCustomerSerializer,
        'EditStatusAndAssignedStatusOfDispenserGunMappingToCustomerSerializer': EditStatusAndAssignedStatusOfDispenserGunMappingToCustomerSerializer,
        'CreateDispenserGunMappingToVehiclesSerializer': CreateDispenserGunMappingToVehiclesSerializer,
        'EditDispenserGunMappingToVehiclesSerializer': EditDispenserGunMappingToVehiclesSerializer,
        'EditStatusAndAssignedStatusOfDispenserGunMappingToVehiclesSerializer': EditStatusAndAssignedStatusOfDispenserGunMappingToVehiclesSerializer,
        'AssignNodeUnitAndDispenserGunMappingToCustomerSerializer': AssignNodeUnitAndDispenserGunMappingToCustomerSerializer,
        'EditNodeDispenserCustomerMappingSerializer': EditNodeDispenserCustomerMappingSerializer,
        'EditStatusAndAssignedStatusOfNodeDispenserCustomerMappingSerializer': EditStatusAndAssignedStatusOfNodeDispenserCustomerMappingSerializer,
        'AddDeliveryLocationMappingDispenserUnitSerializer': AddDeliveryLocationMappingDispenserUnitSerializer,
        'EditDeliveryLocationMappingDispenserUnitSerializer': EditDeliveryLocationMappingDispenserUnitSerializer,
        'GetDispenserGunMappingListByDeliveryLocationIDsSerializer': GetDispenserGunMappingListByDeliveryLocationIDsSerializer,
        'CreateRequestForFuelDispensingSerializer': CreateRequestForFuelDispensingSerializer,
        'AddVINVehicleSerializer': AddVINVehicleSerializer,
        'EditVINVehicleSerializer': EditVINVehicleSerializer,
        'CreateRequestForOrderFuelDispensingSerializer': CreateRequestForOrderFuelDispensingSerializer,
        'VehicleNoSerializer': VehicleNoSerializer,
    }
    _bind_request_serializers(views, _serializer_map)

    annotate_auth(views)
    annotate_customers(views)
    annotate_dispenser_units(views)
    annotate_gun_units(views)
    annotate_node_units(views)
    annotate_dgm_customer(views)
    annotate_dgm_vehicle(views)
    annotate_ndc_mapping(views)
    annotate_dl_mapping(views)
    annotate_fuel_dispensing(views)
    annotate_vin(views)
    annotate_dashboard(views)
    annotate_order_dispensing(views)
    annotate_fuel_readings(views)
