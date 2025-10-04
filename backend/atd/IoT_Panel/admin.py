from django.contrib import admin
from .models import *


admin.site.register(DispenserUnits)
admin.site.register(GunUnits)
admin.site.register(NodeUnits)
admin.site.register(Dispenser_Gun_Mapping_To_Customer)
admin.site.register(NodeDispenserCustomerMapping)
admin.site.register(DeliveryLocation_Mapping_DispenserUnit)