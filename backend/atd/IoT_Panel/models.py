from django.db import models
from existing_tables.models import *
from django.core.validators import MaxValueValidator

# Create your models here.
class DispenserUnits(models.Model):
    id = models.BigAutoField(primary_key=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    imei_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    mac_address = models.CharField(max_length=100, blank=True, null=True, unique=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    hardware_version = models.CharField(max_length=50, blank=True, null=True)
    production_date = models.DateField(blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)   
    assigned_status = models.BooleanField(default=False)
    connectivity_status = models.CharField(max_length=12,blank=True,null=True,db_comment="online/offline/unknown")
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    # deleted_at = models.DateTimeField(blank=True, null=True)
    
   
    class Meta:
        db_table = "dispenser_units"


class GunUnits(models.Model):
    id = models.BigAutoField(primary_key=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    mac_address = models.CharField(max_length=100, unique=True, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    hardware_version = models.CharField(max_length=50, blank=True, null=True)
    production_date = models.DateField(blank=True, null=True)
    rfid_reader_type = models.CharField(max_length=100, blank=True, null=True)   # e.g. UHF, range config
    battery_capacity = models.IntegerField(blank=True, null=True, help_text="mAh")
    backup_hours = models.FloatField(blank=True, null=True, help_text="Estimated backup in hours")
    assigned_status = models.BooleanField(default=False)
    connectivity_status = models.CharField(max_length=12,blank=True,null=True,db_comment="online/offline/unknown")
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    # deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "gun_units"


class NodeUnits(models.Model):
    id = models.BigAutoField(primary_key=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    imei_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    mac_address = models.CharField(max_length=100, unique=True, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    hardware_version = models.CharField(max_length=50, blank=True, null=True)
    production_date = models.DateField(blank=True, null=True)
    battery_capacity = models.IntegerField(blank=True, null=True, help_text="mAh")
    backup_hours = models.FloatField(blank=True, null=True, help_text="Estimated backup in hours")
    assigned_status = models.BooleanField(default=False)
    connectivity_status = models.CharField(max_length=12,blank=True,null=True,db_comment="online/offline/unknown")
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "node_units"


class Dispenser_Gun_Mapping_To_Customer(models.Model):
    Machine_Status = [
        (1, 'Idle'),
        (0, 'Offline'),
        (2, 'Dispensing'),
        (3, 'Allocated'),
        (4, 'Error'),
    ]

    Installation_Mode = [
        (0, 'Static'),
        (1, 'Mobility')
    ]

    Fuel_Level_Sensor_Type = [
        (0, 'None'),
        (1, 'Capacitive')
    ]
    id = models.BigAutoField(primary_key=True)
    dispenser_unit = models.ForeignKey('DispenserUnits', on_delete=models.CASCADE)
    gun_unit = models.ForeignKey('GunUnits', on_delete=models.CASCADE,blank=True, null=True)
    customer = models.BigIntegerField(help_text="Customer ID")
    totalizer_reading = models.FloatField(default=0.00, validators=[MaxValueValidator(99999999.0)],help_text="Totalizer reading value at the time of assigning the dispenser-gun pair to the customer")
    live_totalizer_reading = models.FloatField(default=0.00, validators=[MaxValueValidator(99999999.0)], help_text="Live totalizer reading value")
    total_reading_amount = models.FloatField(default=0.00, help_text="Total amount collected at the time of assigning the dispenser-gun pair to the customer") 
    live_total_reading_amount = models.FloatField(default=0.00, help_text="Live total amount collected so far")
    live_price = models.FloatField(default=0.00, help_text="Current price per liter/unit")
    grade = models.IntegerField(blank=True, null=True, help_text="Fuel grade/type")
    nozzle = models.IntegerField(blank=True, null=True, help_text="Nozzle number")
    gps_coordinates = models.JSONField(blank=True, null=True, help_text="Live GPS coordinates as JSON: {'lat': ..., 'lon': ...}")
    assigned_status = models.BooleanField(default=True, help_text="Whether this unit is currently with customer or not")
    status = models.BooleanField(default=True, help_text="to stop controls to the customer")
    machine_status = models.IntegerField(default=0, choices=Machine_Status, help_text="Machine status")
    connectivity_status = models.BooleanField(default=False, help_text="Whether the machine is connected to the websocket server or not")
    installation_mode = models.IntegerField(default=0, choices=Installation_Mode, help_text="Installation Mode")
    fuel_level_sensor = models.BooleanField(default=False, help_text="Whether the tank is installed with fuel level sensor or not")
    fuel_level_sensor_type = models.IntegerField(default=0, choices=Fuel_Level_Sensor_Type, help_text="Fuel Level Sensor Type")
    fuel_level_sensor_brand = models.CharField(max_length=100,blank=True,null=True,db_comment="Brand of the Fuel Level Sensor")
    tank_capacity = models.FloatField(blank=True,null=True, help_text="Tank Capacity")
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "dispenser_gun_mapping_to_customer"
        verbose_name = "Dispenser-Gun Mapping to Customer"
        verbose_name_plural = "Dispenser-Gun Mappings"



class NodeDispenserCustomerMapping(models.Model):
    id = models.BigAutoField(primary_key=True)
    node_unit = models.ForeignKey(NodeUnits,on_delete=models.CASCADE,related_name="node_mappings",help_text="Node Unit being assigned")
    dispenser_unit = models.ForeignKey(DispenserUnits,on_delete=models.SET_NULL,null=True,blank=True,related_name="dispenser_mappings",help_text="Dispenser Unit (optional) being assigned")
    customer = models.BigIntegerField(help_text="Customer ID to whom both units are assigned")
    fuel_sensor_type = models.IntegerField(help_text="Fuel sensor type, e.g., 0 - ultrasonic, 1 - float, 2 - capacitive")
    assigned_status = models.BooleanField(default=True, help_text="Whether this unit is currently with customer or not")
    status = models.BooleanField(default=True, help_text="to stop controls to the customer")
    gps_coordinates = models.JSONField(blank=True, null=True, help_text="Live GPS coordinates as JSON: {'lat': ..., 'lon': ...}")
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "node_dispenser_customer_mapping"
        verbose_name = "Node-Dispenser Mapping to Customer"
        verbose_name_plural = "Node-Dispenser Mappings"
 

class DeliveryLocation_Mapping_DispenserUnit(models.Model):
    id = models.BigAutoField(primary_key=True)
    dispenser_gun_mapping_id = models.ForeignKey('Dispenser_Gun_Mapping_To_Customer', on_delete=models.CASCADE,null=True,blank=True)
    delivery_location_id = models.BigIntegerField(help_text="Delivery Location ID where dispenser unit is installed")
    DU_Accessible_delivery_locations = models.JSONField(default=list,help_text="Stores a list of delivery location IDs of this customer who can access this dispenser unit")
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "delivery_location_mapping_dispenser_unit"
        verbose_name = "Delivery Location Mapping Dispenser Unit"
        verbose_name_plural = "Delivery Location Mappings"


class RequestFuelDispensingDetails(models.Model):
    # Request_Status = [
    #     (0, 'Pending'),
    #     (1, 'Completed'),
    #     (2, 'Failed'),
    # ]

    Request_Status = [
        (0, 'Pending'),
        (1, 'Hardware Received'),
        (2, 'Dispensiing'),
        (3, 'Completed'),
        (4,'Interrupted'),
        (5,'Failed')
    ]

    Validation_Status = [
        (0, 'True'),
        (1, 'False'),
        (2, 'Pending')
    ]
    Request_Type = [
        (0, 'Volume'),
        (1, 'Amount'),
    ]

    Request_Vehicle = [
        (0, 'Asset'),
        (1, 'VIN'),
    ]
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(help_text="User ID of who is requesting the fuel dispensing")
    user_name = models.CharField(max_length=255,blank=True,null=True, help_text="User Name")
    user_email = models.EmailField(blank=True,null=True, help_text="User Email")
    user_phone = models.CharField(max_length=255,blank=True,null=True, help_text="User Phone")
    dispenser_gun_mapping_id = models.BigIntegerField(help_text="Dispenser Gun Mapping ID")
    dispenser_serialnumber = models.CharField(max_length=255, help_text="Dispenser Unit Serial Number")
    dispenser_imeinumber = models.CharField(max_length=255, help_text="Dispenser Unit IMEI Number")
    delivery_location_id = models.BigIntegerField(help_text="Delivery Location ID of the dispenser unit")
    delivery_location_name = models.CharField(max_length=255, help_text="Delivery Location Name")
    DU_Accessible_delivery_locations = models.JSONField(default=list,blank=True,null=True,help_text="list of delivery location IDs which are accessible to the selected dispenser unit")
    customer_id = models.BigIntegerField(help_text="Customer ID")
    customer_name = models.CharField(max_length=255, help_text="Customer Name")
    customer_email = models.EmailField(blank=True,null=True, help_text="Customer Email")
    customer_phone = models.CharField(max_length=255,blank=True,null=True, help_text="Customer Phone")
    asset_id = models.BigIntegerField(help_text="Asset ID / VIN ID")
    asset_name = models.CharField(max_length=255,blank=True,null=True, help_text="Asset Name /VIN Name")
    asset_tag_id = models.CharField(max_length=255,blank=True,null=True, help_text="Asset Tag ID")
    asset_tag_type = models.CharField(max_length=255,blank=True,null=True, help_text="Asset Tag Type")
    asset_type = models.CharField(max_length=255,blank=True,null=True, help_text="Asset Type")
    transaction_id = models.CharField(max_length=255, help_text="Transaction ID")
    dispenser_volume = models.FloatField(blank=True,null=True, help_text="Dispenser Volume")
    dispenser_price = models.FloatField(blank=True,null=True, help_text="Dispenser Price")
    dispenser_live_price = models.FloatField(blank=True,null=True, help_text="Dispenser Live Price")
    dispenser_received_volume = models.FloatField(blank=True,null=True, help_text="Dispenser Received Volume")
    dispenser_received_price = models.FloatField(blank=True,null=True, help_text="Dispenser Received Price")
    totalizer_volume_starting = models.FloatField(blank=True,null=True, help_text="Totalizer Volume at transaction starting")
    totalizer_volume_ending = models.FloatField(blank=True,null=True, help_text="Totalizer Volume at transaction ending")
    totalizer_price_starting = models.FloatField(blank=True,null=True, help_text="Totalizer Price at transaction starting")
    totalizer_price_ending = models.FloatField(blank=True,null=True, help_text="Totalizer Price at transaction ending")
    gps_coordinates_starting = models.JSONField(blank=True, null=True, help_text="GPS coordinates at transaction starting as JSON: {'lat': ..., 'lon': ...}")
    gps_coordinates_ending = models.JSONField(blank=True, null=True, help_text="GPS coordinates at transaction ending as JSON: {'lat': ..., 'lon': ...}")
    totalizer_validation = models.IntegerField(default=2, choices=Validation_Status, help_text="Totalizer Reading Validation with previous transaction")
    request_vehicle = models.IntegerField(default=0, choices=Request_Vehicle, help_text="Request Vehicle")
    request_type = models.IntegerField(default=0, choices=Request_Type, help_text="Request Type")
    request_status = models.IntegerField(default=0, choices=Request_Status, help_text="Request Status")
    fuel_state = models.BooleanField(default=False)
    transaction_log = models.JSONField(blank=True, null=True, help_text="log of the transaction")
    dispense_end_time = models.DateTimeField(blank=True, null=True, help_text="Fuel Dispense End Time")
    dispense_time_taken = models.FloatField(blank=True, null=True, help_text="Fuel Dispense Time Taken in seconds")
    dispense_status_code = models.IntegerField(default=0,help_text="Fuel Dispenser Status Code")
    remarks = models.CharField(max_length=255, blank=True, null=True, help_text="Remarks")
    request_created_at = models.DateTimeField(blank=True, null=True)
    request_updated_at = models.DateTimeField(blank=True, null=True)
    request_created_by = models.PositiveBigIntegerField(blank=True, null=True)
    request_updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "request_fuel_dispensing_details"
        verbose_name = "Request Fuel Dispensing Details"
        verbose_name_plural = "Request Fuel Dispensing Details"


class VIN_Vehicle(models.Model):
    Tag_type = [
        (1, 'None'),
        (2, 'RFID'),
        (3, 'NFC'),
    ]

    id = models.BigAutoField(primary_key=True)
    vin = models.CharField(max_length=255, help_text="Vehicle Identification Number")
    customer_id = models.BigIntegerField(help_text="Customer ID")
    delivery_location_id = models.JSONField(default=list,help_text="Delivery Location ID")
    point_of_contact_id = models.JSONField(default=list,help_text="Point of Contact ID") 
    vehicle_type = models.CharField(max_length=255, blank=True, null=True, help_text="Vehicle Type from Assets Type Table")
    vehicle_type_name = models.CharField(max_length=255, blank=True, null=True, help_text="Vehicle Type Name from Assets Type Table")
    capacity = models.IntegerField(blank=True, null=True,help_text="Capacity")
    dg_kv = models.BigIntegerField(blank=True, null=True,help_text="DG KV if type is Diesel Generator")
    transaction_id = models.CharField(blank=True,null=True,max_length=255, help_text="Transaction ID")
    dispense_volume = models.FloatField(blank=True,null=True, help_text="max dispense volume given to this vin")
    buffer_dispense_volume  = models.FloatField(blank=True,null=True, help_text="buffer dispense volume given to this vin")
    buffer_reason = models.CharField(max_length=255, blank=True, null=True, help_text="Reason to allocate the buffer volume")
    tag_type = models.CharField(max_length=255, blank=True, null=True, help_text="Tag Type", choices=Tag_type)
    tag_id = models.CharField(max_length=255, blank=True, null=True, help_text="Tag ID")
    status = models.BooleanField(default=False,help_text="whether this vin is used or not once")
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "vin_vehicle"
        verbose_name = "VIN Vehicle"
        verbose_name_plural = "VIN Vehicles"


class Dispenser_Gun_Mapping_To_Vehicles(models.Model):
    Machine_Status = [
        (1, 'Idle'),
        (0, 'Offline'),
        (2, 'Dispensing'),
        (3, 'Allocated'),
        (4, 'Error'),
    ]
    Installation_Mode = [
        (0, 'Static'),
        (1, 'Mobility')
    ]

    Fuel_Level_Sensor_Type = [
        (0, 'None'),
        (1, 'Capacitive')
    ]

    Dispenser_Position = [
        (0, 'Left'),
        (1, 'Right'),
        (2, 'Center'),
    ]

    id = models.BigAutoField(primary_key=True)
    dispenser_unit = models.ForeignKey('DispenserUnits', on_delete=models.CASCADE)
    gun_unit = models.ForeignKey('GunUnits', on_delete=models.CASCADE,blank=True, null=True)
    vehicle = models.BigIntegerField(help_text="Vehicle ID",blank=True, null=True)
    totalizer_reading = models.FloatField(default=0.00, validators=[MaxValueValidator(99999999.0)],help_text="Totalizer reading value at the time of assigning the dispenser-gun pair to the customer")
    live_totalizer_reading = models.FloatField(default=0.00, validators=[MaxValueValidator(99999999.0)], help_text="Live totalizer reading value")
    total_reading_amount = models.FloatField(default=0.00, help_text="Total amount collected at the time of assigning the dispenser-gun pair to the customer") 
    live_total_reading_amount = models.FloatField(default=0.00, help_text="Live total amount collected so far")
    live_price = models.FloatField(default=0.00, help_text="Current price per liter/unit")
    grade = models.IntegerField(blank=True, null=True, help_text="Fuel grade/type")
    nozzle = models.IntegerField(blank=True, null=True, help_text="Nozzle number")
    dispenser_position = models.IntegerField(default=0, choices=Dispenser_Position, help_text="Dispenser Position")
    gps_coordinates = models.JSONField(blank=True, null=True, help_text="Live GPS coordinates as JSON: {'lat': ..., 'lon': ...}")
    assigned_status = models.BooleanField(default=True, help_text="Whether this unit is currently with vehicles or not")
    status = models.BooleanField(default=True, help_text="to stop controls to the vehicles")
    machine_status = models.IntegerField(default=0, choices=Machine_Status, help_text="Machine status")
    connectivity_status = models.BooleanField(default=False, help_text="Whether the machine is connected to the websocket server or not")
    installation_mode = models.IntegerField(default=0, choices=Installation_Mode, help_text="Installation Mode")
    fuel_level_sensor = models.BooleanField(default=False, help_text="Whether the tank is installed with fuel level sensor or not")
    fuel_level_sensor_type = models.IntegerField(default=0, choices=Fuel_Level_Sensor_Type, help_text="Fuel Level Sensor Type")
    fuel_level_sensor_brand = models.CharField(max_length=100,blank=True,null=True,db_comment="Brand of the Fuel Level Sensor")
    tank_capacity = models.FloatField(blank=True,null=True, help_text="Tank Capacity")
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
 
    class Meta:
        db_table = "dispenser_gun_mapping_to_vehicles"
        verbose_name = "Dispenser-Gun Mapping to Vehicles"
        verbose_name_plural = "Dispenser-Gun Mappings to Vehicles"
