from django.db import models

# Create your models here.
# class DispenserUnits(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     serial_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
#     batch_number = models.CharField(max_length=100, blank=True, null=True)
#     imei_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
#     mac_address = models.CharField(max_length=100, blank=True, null=True, unique=True)
#     firmware_version = models.CharField(max_length=50, blank=True, null=True)
#     hardware_version = models.CharField(max_length=50, blank=True, null=True)
#     production_date = models.DateField(blank=True, null=True)
#     remarks = models.CharField(max_length=255, blank=True, null=True)   
#     assigned_status = models.BooleanField(default=False)
#     connectivity_status = models.CharField(max_length=12,blank=True,null=True,db_comment="online/offline/unknown")
#     created_at = models.DateTimeField(blank=True, null=True)
#     updated_at = models.DateTimeField(blank=True, null=True)
#     created_by = models.PositiveBigIntegerField(blank=True, null=True)
#     updated_by = models.PositiveBigIntegerField(blank=True, null=True)
#     deleted_at = models.DateTimeField(blank=True, null=True)
   
#     class Meta:
#         db_table = "dispenser_units"


# class GunUnit(models.Model):
#     serial_number = models.CharField(max_length=100,null=True, blank=True)
#     batch_number = models.CharField(max_length=100,null=True, blank=True)
#     mac_address = models.CharField(max_length=100,null=True, blank=True)
#     remarks = models.CharField(max_length=100,null=True, blank=True)
#     status = models.BooleanField(default=False)