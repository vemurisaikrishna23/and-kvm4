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
    id = models.BigAutoField(primary_key=True)
    dispenser_unit = models.ForeignKey('DispenserUnits', on_delete=models.CASCADE)
    gun_unit = models.ForeignKey('GunUnits', on_delete=models.CASCADE)
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
    remarks = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        db_table = "dispenser_gun_mapping_to_customer"
        verbose_name = "Dispenser-Gun Mapping to Customer"
        verbose_name_plural = "Dispenser-Gun Mappings"

    def __str__(self):
        return f"Map {self.id}: Cust-{self.customer}, Disp-{self.dispenser_unit_id}, Gun-{self.gun_unit_id}"

