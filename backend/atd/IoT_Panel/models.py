from django.db import models

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
    rfid_reader_type = models.CharField(max_length=100, blank=True, null=True)   # e.g. UHF, range config
    battery_capacity = models.IntegerField(blank=True, null=True, help_text="mAh")
    backup_hours = models.FloatField(blank=True, null=True, help_text="Estimated backup in hours")
    assigned_status = models.BooleanField(default=False)
    connectivity_status = models.CharField(max_length=12,blank=True,null=True,db_comment="online/offline/unknown")
    remarks = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    # deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "gun_units"

