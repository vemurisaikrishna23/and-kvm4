from re import U
from rest_framework import serializers
from passlib.hash import bcrypt
from existing_tables.models import *
from .models import *
from django.utils import timezone
from django.db import transaction
import random
import string
from django.utils.crypto import salted_hmac
from django.db.models import Q 


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = Users
        fields = ['email', 'password']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = Users.objects.get(email__iexact=email)
        except Users.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Invalid credentials'})
        if not user.password or not bcrypt.verify(password, user.password):
            raise serializers.ValidationError({'detail': 'Invalid credentials'})
        attrs['user'] = user
        return attrs

class GetCustomersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = '__all__'


class CreateDispenserUnitSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(max_length=100, required=True,allow_blank=False, error_messages={"blank": "This value should not be empty"})
    batch_number = serializers.CharField(max_length=100, required=True,allow_blank=False, error_messages={"blank": "This value should not be empty"})
    imei_number = serializers.CharField(max_length=100, required=True,allow_blank=False, error_messages={"blank": "This value should not be empty"})
    mac_address = serializers.CharField(max_length=100, required=True,allow_blank=False, error_messages={"blank": "This value should not be empty"})
    firmware_version = serializers.CharField(max_length=50, required=True,allow_blank=False, error_messages={"blank": "This value should not be empty"})
    hardware_version = serializers.CharField(max_length=50, required=True,allow_blank=False, error_messages={"blank": "This value should not be empty"})
    production_date = serializers.DateField(required=True,allow_null=False, error_messages={"blank": "This value should not be empty"})
    class Meta:
        model = DispenserUnits
        fields = [
            'serial_number',
            'batch_number',
            'imei_number',
            'mac_address',
            'firmware_version',
            'hardware_version',
            'production_date',
            'remarks'
        ]

    def validate(self, attrs):
        if DispenserUnits.objects.filter(serial_number=attrs['serial_number']).exists():
            raise serializers.ValidationError("Serial number already exists.")
        if DispenserUnits.objects.filter(imei_number=attrs['imei_number']).exists():
            raise serializers.ValidationError("IMEI number already exists.")
        if DispenserUnits.objects.filter(mac_address=attrs['mac_address']).exists():
            raise serializers.ValidationError("MAC address already exists.")
        return attrs

    def create(self, validated_data):
        user = self.context.get("user", None)
        return DispenserUnits.objects.create(
            serial_number=validated_data.get('serial_number'),
            batch_number=validated_data.get('batch_number'),
            imei_number=validated_data.get('imei_number'),
            mac_address=validated_data.get('mac_address'),
            firmware_version=validated_data.get('firmware_version'),
            hardware_version=validated_data.get('hardware_version'),
            production_date=validated_data.get('production_date'),
            remarks=validated_data.get('remarks'),
            created_by=user.id,
            created_at=timezone.now()
        )

class GetDispenserUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispenserUnits
        fields = '__all__'

class EditDispenserUnitSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    batch_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    imei_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    mac_address = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    firmware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    hardware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    production_date = serializers.DateField(required=True,allow_null=False, error_messages={"blank": "This value should not be empty"})

    class Meta:
        model = DispenserUnits
        fields = '__all__'

        def validate(self, attrs):
            instance = getattr(self, 'instance', None)
            serial_number = attrs.get('serial_number')
            if serial_number is not None:
                qs = DispenserUnits.objects.filter(serial_number=serial_number)
                if instance:
                    qs = qs.exclude(pk=instance.pk)
                if qs.exists():
                    raise serializers.ValidationError("Serial number already exists.")
            imei_number = attrs.get('imei_number')
            if imei_number is not None:
                qs = DispenserUnits.objects.filter(imei_number=imei_number)
                if instance:
                    qs = qs.exclude(pk=instance.pk)
                if qs.exists():
                    raise serializers.ValidationError("IMEI number already exists.")
            mac_address = attrs.get('mac_address')
            if mac_address is not None:
                qs = DispenserUnits.objects.filter(mac_address=mac_address)
                if instance:
                    qs = qs.exclude(pk=instance.pk)
                if qs.exists():
                    raise serializers.ValidationError("MAC address already exists.")
            return attrs

    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        instance.serial_number = validated_data.get('serial_number', instance.serial_number)
        instance.imei_number = validated_data.get('imei_number', instance.imei_number)
        instance.mac_address = validated_data.get('mac_address', instance.mac_address)
        instance.firmware_version = validated_data.get('firmware_version', instance.firmware_version)
        instance.hardware_version = validated_data.get('hardware_version', instance.hardware_version)
        instance.production_date = validated_data.get('production_date', instance.production_date)
        instance.remarks = validated_data.get('remarks', instance.remarks)
        instance.updated_by = user.id
        instance.updated_at = timezone.now()
        instance.save()
        return instance

class DeleteDispenserUnitSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    def validate(self, attrs):
        dispenser_id = attrs.get('id')
        try:
            instance = DispenserUnits.objects.get(pk=dispenser_id)
        except DispenserUnits.DoesNotExist:
            raise serializers.ValidationError("Dispenser unit not found.")
        if instance.assigned_status is True:
            raise serializers.ValidationError("This dispenser unit is assigned to the customer.")
        attrs['instance'] = instance
        return attrs


class CreateGunUnitSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    mac_address = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    firmware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    hardware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    rfid_reader_type = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    batch_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    production_date = serializers.DateField(required=True,allow_null=False, error_messages={"blank": "This value should not be empty"})
    class Meta:
        model = GunUnits
        fields = '__all__'
    
    def validate(self, attrs):
        if GunUnits.objects.filter(serial_number=attrs['serial_number']).exists():
            raise serializers.ValidationError("Serial number already exists.")
        if GunUnits.objects.filter(mac_address=attrs['mac_address']).exists():
            raise serializers.ValidationError("MAC address already exists.")
        return attrs
    
    def create(self, validated_data):
        user = self.context.get("user", None)
        return GunUnits.objects.create(
            serial_number=validated_data.get('serial_number'),
            batch_number=validated_data.get('batch_number'),
            mac_address=validated_data.get('mac_address'),
            production_date=validated_data.get('production_date'),
            firmware_version=validated_data.get('firmware_version'),
            hardware_version=validated_data.get('hardware_version'),
            rfid_reader_type=validated_data.get('rfid_reader_type'),
            battery_capacity=validated_data.get('battery_capacity'),
            backup_hours=validated_data.get('backup_hours'),
            remarks=validated_data.get('remarks'),
            created_by=user.id,
            created_at=timezone.now()
        )
    
class GetGunUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GunUnits
        fields = '__all__'

class EditGunUnitSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    mac_address = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    firmware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    hardware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    rfid_reader_type = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    batch_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    production_date = serializers.DateField(required=True,allow_null=False, error_messages={"blank": "This value should not be empty"})

    class Meta:
        model = GunUnits
        fields = '__all__'

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        serial_number = attrs.get('serial_number')
        if serial_number is not None:
            qs = GunUnits.objects.filter(serial_number=serial_number)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Serial number already exists.")
        mac_address = attrs.get('mac_address')
        if mac_address is not None:
            qs = GunUnits.objects.filter(mac_address=mac_address)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError("MAC address already exists.")
        return attrs
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        instance.serial_number = validated_data.get('serial_number', instance.serial_number)
        instance.mac_address = validated_data.get('mac_address', instance.mac_address)
        instance.firmware_version = validated_data.get('firmware_version', instance.firmware_version)
        instance.hardware_version = validated_data.get('hardware_version', instance.hardware_version)
        instance.rfid_reader_type = validated_data.get('rfid_reader_type', instance.rfid_reader_type)
        instance.production_date = validated_data.get('production_date', instance.production_date)
        instance.battery_capacity = validated_data.get('battery_capacity', instance.battery_capacity)
        instance.backup_hours = validated_data.get('backup_hours', instance.backup_hours)
        instance.remarks = validated_data.get('remarks', instance.remarks)
        instance.updated_by = user.id
        instance.updated_at = timezone.now()
        instance.save()
        return instance


class DeleteGunUnitSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    def validate(self, attrs):
        gun_unit_id = attrs.get('id')
        try:
            instance = GunUnits.objects.get(pk=gun_unit_id)
        except GunUnits.DoesNotExist:
            raise serializers.ValidationError("Gun unit not found.")
        if instance.assigned_status is True:
            raise serializers.ValidationError("This Gun unit is assigned to the Dispenser Unit.")
        attrs['instance'] = instance
        return attrs
    
    
class CreateNodeUnitSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    imei_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    mac_address = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    firmware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    hardware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    batch_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    production_date = serializers.DateField(required=True,allow_null=False, error_messages={"blank": "This value should not be empty"})
    class Meta:
        model = NodeUnits
        fields = '__all__'
    
    def validate(self, attrs):
        if NodeUnits.objects.filter(serial_number=attrs['serial_number']).exists():
            raise serializers.ValidationError("Serial number already exists.")
        if NodeUnits.objects.filter(imei_number=attrs['imei_number']).exists():
            raise serializers.ValidationError("IMEI number already exists.")
        if NodeUnits.objects.filter(mac_address=attrs['mac_address']).exists():
            raise serializers.ValidationError("MAC address already exists.")
        return attrs
    
    def create(self, validated_data):
        user = self.context.get("user", None)
        return NodeUnits.objects.create(
            serial_number=validated_data.get('serial_number'),
            imei_number=validated_data.get('imei_number'),
            batch_number=validated_data.get('batch_number'),
            mac_address=validated_data.get('mac_address'),
            firmware_version=validated_data.get('firmware_version'),
            production_date=validated_data.get('production_date'),
            hardware_version=validated_data.get('hardware_version'),
            battery_capacity=validated_data.get('battery_capacity'),
            backup_hours=validated_data.get('backup_hours'),
            remarks=validated_data.get('remarks'),
            created_by=user.id,
            created_at=timezone.now()
        )

class GetNodeUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeUnits
        fields = '__all__'


class EditNodeUnitSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    imei_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    mac_address = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    firmware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    hardware_version = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    batch_number = serializers.CharField(required=True, allow_blank=False, error_messages={"blank": "This value should not be empty"})
    production_date = serializers.DateField(required=True,allow_null=False, error_messages={"blank": "This value should not be empty"})

    class Meta:
        model = NodeUnits
        fields = '__all__'

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        serial_number = attrs.get('serial_number')
        if serial_number is not None:
            qs = NodeUnits.objects.filter(serial_number=serial_number)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Serial number already exists.")
        
        imei_number = attrs.get('imei_number')
        if imei_number is not None:
            qs = NodeUnits.objects.filter(imei_number=imei_number)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError("IMEI number already exists.")
        
        mac_address = attrs.get('mac_address')
        if mac_address is not None:
            qs = NodeUnits.objects.filter(mac_address=mac_address)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError("MAC address already exists.")
        return attrs
    
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        instance.serial_number = validated_data.get('serial_number', instance.serial_number)
        instance.imei_number = validated_data.get('imei_number', instance.imei_number)
        instance.mac_address = validated_data.get('mac_address', instance.mac_address)
        instance.firmware_version = validated_data.get('firmware_version', instance.firmware_version)
        instance.hardware_version = validated_data.get('hardware_version', instance.hardware_version)
        instance.battery_capacity = validated_data.get('battery_capacity', instance.battery_capacity)
        instance.backup_hours = validated_data.get('backup_hours', instance.backup_hours)
        instance.batch_number = validated_data.get('batch_number', instance.batch_number)
        instance.production_date = validated_data.get('production_date', instance.production_date)
        instance.remarks = validated_data.get('remarks', instance.remarks)
        instance.updated_by = user.id
        instance.updated_at = timezone.now()
        instance.save()
        return instance


class DeleteNodeUnitSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate(self, attrs):
        node_unit_id = attrs.get('id')
        try:
            instance = NodeUnits.objects.get(pk=node_unit_id)
        except NodeUnits.DoesNotExist:
            raise serializers.ValidationError("Node unit not found.")
        if instance.assigned_status is True:
            raise serializers.ValidationError("This Node unit is assigned to the Customer Unit.")
        attrs['instance'] = instance
        return attrs

class CreateDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    customer = serializers.IntegerField(required=True)
    dispenser_unit = serializers.PrimaryKeyRelatedField(
        queryset=DispenserUnits.objects.all(),
        required=True
    )
    gun_unit = serializers.PrimaryKeyRelatedField(
        queryset=GunUnits.objects.all(),
        required=False,
        allow_null=True
    )
    totalizer_reading = serializers.FloatField(required=True)
    total_reading_amount = serializers.FloatField(required=True)
    live_price = serializers.FloatField(required=True)
    grade = serializers.IntegerField(required=True)
    nozzle = serializers.IntegerField(required=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor = serializers.BooleanField(required=False, default=False)
    fuel_level_sensor_type = serializers.IntegerField(required=False, allow_null=True)
    fuel_level_sensor_brand = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_configuration = serializers.JSONField(required=False, allow_null=True)
    tank_capacity = serializers.FloatField(required=False, allow_null=True)
    class Meta:
        model = Dispenser_Gun_Mapping_To_Customer
        fields = [
            'customer',
            'dispenser_unit',
            'gun_unit',
            'totalizer_reading',
            'total_reading_amount',
            'live_price',
            'grade',
            'nozzle',
            'remarks',
            'fuel_level_sensor',
            'fuel_level_sensor_type',
            'fuel_level_sensor_brand',
            'fuel_level_sensor_description',
            'fuel_level_sensor_configuration',
            'tank_capacity',
        ]

    def validate_customer(self, value):
        if not Customers.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Customer does not exist.")
        return value

    def validate(self, attrs):
        dispenser_unit = attrs.get('dispenser_unit')
        gun_unit = attrs.get('gun_unit')

        if dispenser_unit and dispenser_unit.assigned_status:
            raise serializers.ValidationError(
                "This dispenser unit is already assigned and cannot be allotted."
            )
        if gun_unit and gun_unit.assigned_status:
            raise serializers.ValidationError(
                "This gun unit is already assigned and cannot be allotted."
            )
        fuel_sensor_enabled = attrs.get('fuel_level_sensor', False)
        fuel_related_fields = [
            'fuel_level_sensor_type',
            'fuel_level_sensor_brand',
            'fuel_level_sensor_description',
            'fuel_level_sensor_configuration',
        ]
        fuel_data_provided = any(attrs.get(field) not in [None, '', {}] for field in fuel_related_fields)
        if fuel_data_provided and not fuel_sensor_enabled:
            raise serializers.ValidationError({
                "fuel_level_sensor": (
                    "fuel_level_sensor must be enabled to provide fuel level sensor details."
                )
            })
        if fuel_sensor_enabled is False and fuel_data_provided:
            raise serializers.ValidationError(
                "Fuel level sensor details cannot be provided when fuel_level_sensor is disabled."
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user", None)
        dispenser_unit = validated_data['dispenser_unit']
        gun_unit = validated_data.get('gun_unit')
        if DispenserUnits.objects.select_for_update().get(
            pk=dispenser_unit.pk
        ).assigned_status:
            raise serializers.ValidationError(
                "This dispenser unit is already assigned and cannot be allotted."
            )
        if gun_unit:
            if GunUnits.objects.select_for_update().get(
                pk=gun_unit.pk
            ).assigned_status:
                raise serializers.ValidationError(
                    "This gun unit is already assigned and cannot be allotted."
                )

        instance = Dispenser_Gun_Mapping_To_Customer.objects.create(
            customer=validated_data['customer'],
            dispenser_unit=dispenser_unit,
            gun_unit=gun_unit,
            totalizer_reading=validated_data['totalizer_reading'],
            total_reading_amount=validated_data['total_reading_amount'],
            live_price=validated_data['live_price'],
            grade=validated_data['grade'],
            nozzle=validated_data['nozzle'],
            remarks=validated_data.get('remarks'),
            fuel_level_sensor=validated_data.get('fuel_level_sensor', False),
            fuel_level_sensor_type=validated_data.get('fuel_level_sensor_type'),
            fuel_level_sensor_brand=validated_data.get('fuel_level_sensor_brand'),
            fuel_level_sensor_description=validated_data.get('fuel_level_sensor_description'),
            fuel_level_sensor_configuration=validated_data.get('fuel_level_sensor_configuration'), 
            tank_capacity=validated_data.get('tank_capacity'), 
            created_by=(user.id if user else None),
            created_at=timezone.now(),
        )
        dispenser_unit.assigned_status = True
        dispenser_unit.updated_by = user.id if user else dispenser_unit.updated_by
        dispenser_unit.updated_at = timezone.now()
        dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        if gun_unit:
            gun_unit.assigned_status = True
            gun_unit.updated_by = user.id if user else gun_unit.updated_by
            gun_unit.updated_at = timezone.now()
            gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

        return instance


class LastFuelSensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelSensorReadings
        fields = [
            "fuel_level",
            "temperature",
            "epoch_time",
            "data_type",
            "transaction_id"
        ]

class GetDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    dispenser_unit = GetDispenserUnitsSerializer()
    gun_unit = GetGunUnitsSerializer()
    last_fuel_reading = serializers.SerializerMethodField()

    class Meta:
        model = Dispenser_Gun_Mapping_To_Customer
        fields = '__all__'
        depth = 1

    def get_last_fuel_reading(self, obj):
        last = FuelSensorReadings.objects.filter(
            dispenser_customer_mapping=obj
        ).order_by("-epoch_time").first()

        if not last:
            return {
                "fuel_level": None,
                "temperature": None,
                "epoch_time": None,
                "data_type": None,
                "transaction_id": None
            }

        return LastFuelSensorReadingSerializer(last).data

class EditDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    dispenser_unit = serializers.PrimaryKeyRelatedField(
        queryset=DispenserUnits.objects.all(),
        required=False
    )
    gun_unit = serializers.PrimaryKeyRelatedField(
        queryset=GunUnits.objects.all(),
        required=False,
        allow_null=True
    )
    totalizer_reading = serializers.FloatField(required=False)
    total_reading_amount = serializers.FloatField(required=False)
    live_price = serializers.FloatField(required=False)
    grade = serializers.IntegerField(required=False)
    nozzle = serializers.IntegerField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    fuel_level_sensor = serializers.BooleanField(required=False)
    fuel_level_sensor_type = serializers.IntegerField(required=False, allow_null=True)
    fuel_level_sensor_brand = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_configuration = serializers.JSONField(required=False, allow_null=True)
    
    tank_capacity = serializers.FloatField(required=False, allow_null=True)
    class Meta:
        model = Dispenser_Gun_Mapping_To_Customer
        fields = [
            'dispenser_unit',
            'gun_unit',
            'totalizer_reading',
            'total_reading_amount',
            'live_price',
            'grade',
            'nozzle',
            'remarks',
            'fuel_level_sensor',
            'fuel_level_sensor_type',
            'fuel_level_sensor_brand',
            'fuel_level_sensor_description',
            'fuel_level_sensor_configuration',
            'tank_capacity',
        ]
    def validate(self, attrs):
        instance = self.instance
        if not instance:
            raise serializers.ValidationError("Instance not found.")

        fuel_sensor = attrs.get('fuel_level_sensor', instance.fuel_level_sensor)

        fuel_fields = [
            attrs.get('fuel_level_sensor_type', instance.fuel_level_sensor_type),
            attrs.get('fuel_level_sensor_brand', instance.fuel_level_sensor_brand),
            attrs.get('fuel_level_sensor_description', instance.fuel_level_sensor_description),
            attrs.get('fuel_level_sensor_configuration', instance.fuel_level_sensor_configuration),
        ]

        fuel_data_provided = any(v not in [None, '', {}] for v in fuel_fields)

        if fuel_data_provided and not fuel_sensor:
            raise serializers.ValidationError({
                "fuel_level_sensor": "fuel_level_sensor must be enabled to provide fuel sensor details."
            })

        new_dispenser = attrs.get('dispenser_unit', serializers.empty)
        if new_dispenser is not serializers.empty and new_dispenser != instance.dispenser_unit:
            if new_dispenser.assigned_status:
                raise serializers.ValidationError(
                    "This dispenser unit is already assigned and cannot be allotted."
                )

            attrs['_new_dispenser_unit'] = new_dispenser
            attrs['_previous_dispenser_unit'] = instance.dispenser_unit

        new_gun = attrs.get('gun_unit', serializers.empty)
        if new_gun is not serializers.empty and new_gun != instance.gun_unit:
            if new_gun is not None and new_gun.assigned_status:
                raise serializers.ValidationError(
                    "This gun unit is already assigned and cannot be allotted."
                )

            attrs['_new_gun_unit'] = new_gun
            attrs['_previous_gun_unit'] = instance.gun_unit
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        for field in [
            'totalizer_reading',
            'total_reading_amount',
            'live_price',
            'grade',
            'nozzle',
            'remarks',
            'tank_capacity',
        ]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        fuel_level_sensor = validated_data.get(
            'fuel_level_sensor', instance.fuel_level_sensor
        )

        instance.fuel_level_sensor = fuel_level_sensor

        if fuel_level_sensor:
            instance.fuel_level_sensor_type = validated_data.get(
                'fuel_level_sensor_type', instance.fuel_level_sensor_type
            )
            instance.fuel_level_sensor_brand = validated_data.get(
                'fuel_level_sensor_brand', instance.fuel_level_sensor_brand
            )
            instance.fuel_level_sensor_description = validated_data.get(
                'fuel_level_sensor_description', instance.fuel_level_sensor_description
            )
            instance.fuel_level_sensor_configuration = validated_data.get(
                'fuel_level_sensor_configuration', instance.fuel_level_sensor_configuration
            )
        else:
            instance.fuel_level_sensor_type = None
            instance.fuel_level_sensor_brand = None
            instance.fuel_level_sensor_description = None
            instance.fuel_level_sensor_configuration = None

        if '_new_dispenser_unit' in validated_data:
            new_du = DispenserUnits.objects.select_for_update().get(
                pk=validated_data['_new_dispenser_unit'].pk
            )
            prev_du = DispenserUnits.objects.select_for_update().get(
                pk=validated_data['_previous_dispenser_unit'].pk
            )

            if new_du.assigned_status:
                raise serializers.ValidationError(
                    "This dispenser unit is already assigned."
                )

            instance.dispenser_unit = new_du
            new_du.assigned_status = True
            new_du.updated_by = user.id if user else new_du.updated_by
            new_du.updated_at = timezone.now()
            new_du.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            prev_du.assigned_status = False
            prev_du.updated_by = user.id if user else prev_du.updated_by
            prev_du.updated_at = timezone.now()
            prev_du.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

        if '_new_gun_unit' in validated_data:
            prev_gun = validated_data['_previous_gun_unit']
            new_gun = validated_data['_new_gun_unit']

            if prev_gun:
                prev_gun = GunUnits.objects.select_for_update().get(pk=prev_gun.pk)
                prev_gun.assigned_status = False
                prev_gun.updated_by = user.id if user else prev_gun.updated_by
                prev_gun.updated_at = timezone.now()
                prev_gun.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

            if new_gun:
                new_gun = GunUnits.objects.select_for_update().get(pk=new_gun.pk)
                if new_gun.assigned_status:
                    raise serializers.ValidationError(
                        "This gun unit is already assigned."
                    )

                new_gun.assigned_status = True
                new_gun.updated_by = user.id if user else new_gun.updated_by
                new_gun.updated_at = timezone.now()
                new_gun.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

                instance.gun_unit = new_gun
            else:
                instance.gun_unit = None

        instance.updated_by = user.id if user else instance.updated_by
        instance.updated_at = timezone.now()
        instance.save()
        return instance


class EditStatusAndAssignedStatusOfDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(required=False)
    assigned_status = serializers.BooleanField(required=False)
    
    class Meta:
        model = Dispenser_Gun_Mapping_To_Customer
        fields = ['status', 'assigned_status']
        
    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        if 'status' in attrs and 'assigned_status' in attrs:
            raise serializers.ValidationError("Only one field can be updated at a time: either 'status' or 'assigned_status'.")
        
        if 'status' not in attrs and 'assigned_status' not in attrs:
            raise serializers.ValidationError("Either 'status' or 'assigned_status' must be provided.")
            
        return attrs
        
    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        
        if 'status' in validated_data:
            instance.status = validated_data['status']
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
            
        elif 'assigned_status' in validated_data:
            new_assigned_status = validated_data['assigned_status']
            instance.assigned_status = new_assigned_status
            
            if not new_assigned_status:
                instance.status = False
            
            dispenser_unit = instance.dispenser_unit
            dispenser_unit.assigned_status = new_assigned_status
            dispenser_unit.updated_by = (user.id if user else dispenser_unit.updated_by)
            dispenser_unit.updated_at = timezone.now()
            dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            gun_unit = instance.gun_unit
            if gun_unit is not None:
                gun_unit.assigned_status = new_assigned_status
                gun_unit.updated_by = (user.id if user else gun_unit.updated_by)
                gun_unit.updated_at = timezone.now()
                gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
        
        return instance


class DeleteDispenserGunMappingToCustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
    def validate(self, attrs):
        instance = self.context.get('instance')
        if not instance:
            raise serializers.ValidationError("Instance not found.")        
        if instance.assigned_status is True:
            raise serializers.ValidationError("Cannot delete dispenser gun mapping that is currently assigned to a customer.")
        return attrs
    
    def delete(self, instance):
        instance.delete()
        return instance


class AssignNodeUnitAndDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    node_unit = serializers.PrimaryKeyRelatedField(queryset=NodeUnits.objects.all(), required=True)
    dispenser_unit = serializers.PrimaryKeyRelatedField(queryset=DispenserUnits.objects.all(), required=False, allow_null=True)
    customer = serializers.IntegerField(required=True)
    fuel_sensor_type = serializers.IntegerField(required=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = NodeDispenserCustomerMapping
        fields = ['node_unit', 'dispenser_unit', 'customer', 'fuel_sensor_type', 'remarks']
    
    def validate_customer(self, value):
        if not Customers.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Customer does not exist.")
        return value
    
    def validate_node_unit(self, value):
        if value.assigned_status is True:
            raise serializers.ValidationError("This node unit is already assigned and cannot be allotted.")
        return value
    
    def validate_dispenser_unit(self, value):
        if value and value.assigned_status is False:
            raise serializers.ValidationError("This dispenser unit is not assigned to any customer.")
        return value
    
    def validate(self, attrs):
        node_unit = attrs.get('node_unit')
        dispenser_unit = attrs.get('dispenser_unit')
        customer = attrs.get('customer')
        
        if NodeDispenserCustomerMapping.objects.filter(node_unit=node_unit).exists():
            raise serializers.ValidationError("Node unit already assigned to a customer.")
        
        if dispenser_unit:
            existing_mapping = Dispenser_Gun_Mapping_To_Customer.objects.filter(
                dispenser_unit=dispenser_unit,
                customer=customer,
                assigned_status=True
            ).exists()
            
            if not existing_mapping:
                raise serializers.ValidationError("This dispenser unit is not assigned to this customer.")
        return attrs
        
    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user", None)
        node_unit = validated_data['node_unit']
        dispenser_unit = validated_data.get('dispenser_unit')
        customer = validated_data['customer']
        fuel_sensor_type = validated_data['fuel_sensor_type']
        remarks = validated_data.get('remarks')
        
        if NodeUnits.objects.select_for_update().get(pk=node_unit.pk).assigned_status:
            raise serializers.ValidationError("This node unit is already assigned and cannot be allotted.")
        
        if NodeDispenserCustomerMapping.objects.select_for_update().filter(dispenser_unit=dispenser_unit).exists():
            raise serializers.ValidationError("This dispenser unit is already assigned to another node unit.")

        instance = NodeDispenserCustomerMapping.objects.create(
            node_unit=node_unit,
            dispenser_unit=dispenser_unit,
            customer=customer,
            fuel_sensor_type=fuel_sensor_type,
            remarks=remarks,
            created_by=user.id,
            created_at=timezone.now()
        )        
        node_unit.assigned_status = True
        node_unit.updated_by = user.id
        node_unit.updated_at = timezone.now()
        node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        return instance


class GetNodeDispenserCustomerMappingSerializer(serializers.ModelSerializer):
    node_unit = GetNodeUnitsSerializer()
    dispenser_unit = GetDispenserUnitsSerializer()
    class Meta:
        model = NodeDispenserCustomerMapping
        fields = '__all__'
        depth = 1

class EditNodeDispenserCustomerMappingSerializer(serializers.ModelSerializer):
    node_unit = serializers.PrimaryKeyRelatedField(queryset=NodeUnits.objects.all(), required=False)
    dispenser_unit = serializers.PrimaryKeyRelatedField(queryset=DispenserUnits.objects.all(), required=False, allow_null=True)
    fuel_sensor_type = serializers.IntegerField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = NodeDispenserCustomerMapping
        fields = ['node_unit','dispenser_unit','fuel_sensor_type','remarks',]

    def validate_node_unit(self, value):
        if value and value.assigned_status is True:
            raise serializers.ValidationError("This node unit is already assigned and cannot be allotted.")
        return value

    def validate_dispenser_unit(self, value):
        if value and value.assigned_status is False:
            raise serializers.ValidationError("This dispenser unit is not assigned to any customer.")
        return value

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        previous_data = {
            'node_unit': instance.node_unit,
            'dispenser_unit': instance.dispenser_unit,
            'fuel_sensor_type': instance.fuel_sensor_type,
            'remarks': instance.remarks,
        }

        new_node_unit = attrs.get('node_unit')
        if new_node_unit and new_node_unit != previous_data['node_unit']:
            if NodeDispenserCustomerMapping.objects.filter(node_unit=new_node_unit).exclude(id=instance.id).exists():
                raise serializers.ValidationError("This node unit is already assigned to another customer.")
            
            attrs['_new_node_unit'] = new_node_unit
            attrs['_previous_node_unit'] = previous_data['node_unit']

        new_dispenser_unit = attrs.get('dispenser_unit')
        if new_dispenser_unit != previous_data['dispenser_unit']:
            if new_dispenser_unit:
                existing_mapping = Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    dispenser_unit=new_dispenser_unit,
                    customer=instance.customer,
                    assigned_status=True
                ).exists()
                
                if not existing_mapping:
                    raise serializers.ValidationError("This dispenser unit is not assigned to this customer.")
            
                existing_node_mapping = NodeDispenserCustomerMapping.objects.filter(
                    dispenser_unit=new_dispenser_unit
                ).exclude(id=instance.id).exists()
                
                if existing_node_mapping:
                    raise serializers.ValidationError("This dispenser unit is already assigned to another node unit.")            
            attrs['_new_dispenser_unit'] = new_dispenser_unit
            attrs['_previous_dispenser_unit'] = previous_data['dispenser_unit']
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)        
        previous_data = {
            'node_unit': instance.node_unit,
            'dispenser_unit': instance.dispenser_unit,
            'fuel_sensor_type': instance.fuel_sensor_type,
            'remarks': instance.remarks,
        }
        instance.fuel_sensor_type = validated_data.get('fuel_sensor_type', previous_data['fuel_sensor_type'])
        instance.remarks = validated_data.get('remarks', previous_data['remarks'])        
        if '_new_node_unit' in validated_data:
            new_node_unit = validated_data['_new_node_unit']
            previous_node_unit = validated_data['_previous_node_unit']
            
            instance.node_unit = new_node_unit            
            new_node_unit.assigned_status = True
            new_node_unit.updated_by = (user.id if user else new_node_unit.updated_by)
            new_node_unit.updated_at = timezone.now()
            new_node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])            
            previous_node_unit.assigned_status = False
            previous_node_unit.updated_by = (user.id if user else previous_node_unit.updated_by)
            previous_node_unit.updated_at = timezone.now()
            previous_node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        else:
            instance.node_unit = previous_data['node_unit']
        if '_new_dispenser_unit' in validated_data:
            new_dispenser_unit = validated_data['_new_dispenser_unit']
            instance.dispenser_unit = new_dispenser_unit
        else:
            instance.dispenser_unit = previous_data['dispenser_unit']
        instance.updated_by = (user.id if user else instance.updated_by)
        instance.updated_at = timezone.now()
        instance.save()
        return instance


class EditStatusAndAssignedStatusOfNodeDispenserCustomerMappingSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(required=False)
    assigned_status = serializers.BooleanField(required=False)
    
    class Meta:
        model = NodeDispenserCustomerMapping
        fields = ['status', 'assigned_status']
        
    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        if 'status' in attrs and 'assigned_status' in attrs:
            raise serializers.ValidationError("Only one field can be updated at a time: either 'status' or 'assigned_status'.")        
        if 'status' not in attrs and 'assigned_status' not in attrs:
            raise serializers.ValidationError("Either 'status' or 'assigned_status' must be provided.")
        return attrs
    
    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        if 'status' in validated_data:
            instance.status = validated_data['status']
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
        elif 'assigned_status' in validated_data:
            new_assigned_status = validated_data['assigned_status']
            instance.assigned_status = new_assigned_status            
            if not new_assigned_status:
                instance.status = False
            instance.node_unit.assigned_status = False
            instance.node_unit.updated_by = user.id
            instance.node_unit.updated_at = timezone.now()
            instance.node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])  
        instance.save()          
        return instance


class DeleteNodeDispenserCustomerMappingSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    def validate(self, attrs):
        instance = self.context.get('instance')
        if not instance:
            raise serializers.ValidationError("Instance not found.")        
        if instance.assigned_status is True:
            raise serializers.ValidationError("Cannot delete node dispenser customer mapping that is currently assigned to a customer.")
        return attrs
    def delete(self, instance):
        instance.delete()
        return instance 

class GetDispenserGunMappingListByDeliveryLocationIDsSerializer(serializers.Serializer):
    delivery_location_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    def validate(self, data):
        delivery_location_ids = data.get("delivery_location_ids", [])
        user = self.context.get("user")
        roles = self.context.get("roles", [])

        if not delivery_location_ids:
            raise serializers.ValidationError("delivery_location_ids is required.")
        existing_ids = list(
            DeliveryLocations.objects.filter(id__in=delivery_location_ids).values_list("id", flat=True)
        )

        accessible_ids = list(
            DeliveryLocation_Mapping_DispenserUnit.objects.filter(
                DU_Accessible_delivery_locations__overlap=delivery_location_ids
            ).values_list("DU_Accessible_delivery_locations", flat=True)
        )

        accessible_ids_flat = set()
        for sublist in accessible_ids:
            accessible_ids_flat.update(sublist)

        found_ids = set(existing_ids) | (set(delivery_location_ids) & accessible_ids_flat)
        missing_ids = set(delivery_location_ids) - found_ids
        if missing_ids:
            raise serializers.ValidationError(
                f"Delivery Location IDs not found: {', '.join(map(str, missing_ids))}"
            )
        if ["IOT Admin"] in roles:
            return data
        user_customer_ids = PointOfContacts.objects.filter(
            user_id=user.id,
            belong_to_type="customer"
        ).values_list("belong_to_id", flat=True)

        for dl_id in found_ids:
            try:
                dl_obj = DeliveryLocations.objects.get(id=dl_id)
                if dl_obj.customer_id not in user_customer_ids:
                    raise serializers.ValidationError(
                        f"You are not authorized to access Delivery Location ID {dl_id} (belongs to another customer)."
                    )
            except DeliveryLocations.DoesNotExist:
                continue

        return data



class AddDeliveryLocationMappingDispenserUnitSerializer(serializers.ModelSerializer):
    delivery_location_id = serializers.IntegerField(required=True)
    dispenser_gun_mapping_id = serializers.IntegerField(required=True)
    DU_Accessible_delivery_locations = serializers.JSONField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = DeliveryLocation_Mapping_DispenserUnit
        fields = ['delivery_location_id', 'dispenser_gun_mapping_id', 'DU_Accessible_delivery_locations','remarks']

    def validate_delivery_location_id(self, value):
        if not DeliveryLocations.objects.filter(id=value).exists():
            raise serializers.ValidationError("Delivery location does not exist.")
        return value

    def validate_dispenser_gun_mapping_id(self, value):
        if not Dispenser_Gun_Mapping_To_Customer.objects.filter(id=value).exists():
            raise serializers.ValidationError("Dispenser gun mapping does not exist.")
        return value
    
    def validate(self, attrs):
        delivery_location_id = attrs.get('delivery_location_id')
        dispenser_gun_mapping_id = attrs.get('dispenser_gun_mapping_id')
        DU_Accessible_delivery_locations = attrs.get('DU_Accessible_delivery_locations')
        
        roles = self.context.get("roles", [])

        if DeliveryLocation_Mapping_DispenserUnit.objects.filter(delivery_location_id=delivery_location_id).exists():
            raise serializers.ValidationError("This delivery location id is already exists.")
                
        if DeliveryLocation_Mapping_DispenserUnit.objects.filter(dispenser_gun_mapping_id=dispenser_gun_mapping_id).exists():
            raise serializers.ValidationError("This dispenser gun mapping is already assigned to a delivery location.")
        
        if 'Accounts Admin' in roles:
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                poc = PointOfContacts.objects.filter(
                    user_id=self.context["user"].id,
                    belong_to_type="customer"
                ).first()

                if not poc or poc.belong_to_id != customer_id:
                    raise serializers.ValidationError("You are not authorized to assign this dispenser gun mapping. It belongs to a different customer.")

                if not DeliveryLocations.objects.filter(id=delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("You can only add delivery locations that belong to your customer.")
                
                if DU_Accessible_delivery_locations:
                    for location_id in DU_Accessible_delivery_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"Delivery location with ID {location_id} does not belong to your customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")
        
        elif 'IOT Admin' in roles:
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                if not DeliveryLocations.objects.filter(id=delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("All delivery locations must belong to the same customer as the dispenser gun mapping.")
                
                if DU_Accessible_delivery_locations:
                    for location_id in DU_Accessible_delivery_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"All delivery locations must belong to the same customer. Location ID {location_id} belongs to a different customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")
        
        if DU_Accessible_delivery_locations:
            if not isinstance(DU_Accessible_delivery_locations, list):
                raise serializers.ValidationError("DU_Accessible_delivery_locations must be a list.")
            
            for location_id in DU_Accessible_delivery_locations:
                if not isinstance(location_id, int):
                    raise serializers.ValidationError(f"Invalid delivery location ID: {location_id}. Must be an integer.")
                if not DeliveryLocations.objects.filter(id=location_id).exists():
                    raise serializers.ValidationError(f"Delivery delivery location with ID {location_id} does not exist.")
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user", None)
        delivery_location_id = validated_data['delivery_location_id']
        dispenser_gun_mapping_id = Dispenser_Gun_Mapping_To_Customer.objects.get(id=validated_data['dispenser_gun_mapping_id'])
        DU_Accessible_delivery_locations = validated_data.get('DU_Accessible_delivery_locations', [])
        remarks = validated_data.get('remarks')
        instance = DeliveryLocation_Mapping_DispenserUnit.objects.create(
            delivery_location_id=delivery_location_id,
            dispenser_gun_mapping_id=dispenser_gun_mapping_id,
            DU_Accessible_delivery_locations=DU_Accessible_delivery_locations,
            remarks=remarks,
            created_by=user.id,
            created_at=timezone.now()
        )
        return instance


class GetDeliveryLocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLocations
        fields = '__all__'


class GetDeliveryLocationMappingDispenserUnitSerializer(serializers.ModelSerializer):
    dispenser_gun_mapping_id = GetDispenserGunMappingToCustomerSerializer()
    class Meta:
        model = DeliveryLocation_Mapping_DispenserUnit
        fields = '__all__'
        depth = 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        if instance.delivery_location_id:
            try:
                delivery_location = DeliveryLocations.objects.get(id=instance.delivery_location_id)
                data['delivery_location_id'] = {
                    'id': delivery_location.id,
                    'name': delivery_location.name,
                }
            except DeliveryLocations.DoesNotExist:
                data['delivery_location'] = None
        else:
            data['delivery_location'] = None

        if instance.DU_Accessible_delivery_locations:
            accessible_locations = []
            for location_id in instance.DU_Accessible_delivery_locations:
                try:
                    location = DeliveryLocations.objects.get(id=location_id)
                    accessible_locations.append({
                        'id': location.id,
                        'name': location.name,
                    })
                except DeliveryLocations.DoesNotExist:
                    accessible_locations.append({
                        'id': location_id,
                        'name': f"Unknown Location (ID: {location_id})",
                        'customer': None,
                    })
            data['DU_Accessible_delivery_locations'] = accessible_locations
        else:
            data['DU_Accessible_delivery_locations'] = []
        return data

        

class EditDeliveryLocationMappingDispenserUnitSerializer(serializers.ModelSerializer):
    delivery_location_id = serializers.IntegerField(required=False)
    dispenser_gun_mapping_id = serializers.IntegerField(required=False)
    DU_Accessible_delivery_locations = serializers.JSONField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = DeliveryLocation_Mapping_DispenserUnit
        fields = ['delivery_location_id', 'dispenser_gun_mapping_id', 'DU_Accessible_delivery_locations', 'remarks']

    def validate_delivery_location_id(self, value):
        if value is not None and not DeliveryLocations.objects.filter(id=value).exists():
            raise serializers.ValidationError("Delivery location does not exist.")
        return value

    def validate_dispenser_gun_mapping_id(self, value):
        if value is not None and not Dispenser_Gun_Mapping_To_Customer.objects.filter(id=value).exists():
            raise serializers.ValidationError("Dispenser gun mapping does not exist.")
        return value

    def validate_DU_Accessible_delivery_locations(self, value):
        if value is not None:
            if not isinstance(value, list):
                raise serializers.ValidationError("DU_Accessible_delivery_locations must be a list.")
            
            for location_id in value:
                if not isinstance(location_id, int):
                    raise serializers.ValidationError(f"Invalid location ID: {location_id}. Must be an integer.")
                if not DeliveryLocations.objects.filter(id=location_id).exists():
                    raise serializers.ValidationError(f"Delivery location with ID {location_id} does not exist.")
        return value

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")

        previous_data = {
            'delivery_location_id': instance.delivery_location_id,
            'dispenser_gun_mapping_id': instance.dispenser_gun_mapping_id.id if instance.dispenser_gun_mapping_id else None,
            'DU_Accessible_delivery_locations': instance.DU_Accessible_delivery_locations or [],
            'remarks': instance.remarks,
        }

        roles = self.context.get("roles", [])

        new_dispenser_gun_mapping_id = attrs.get('dispenser_gun_mapping_id')
        if new_dispenser_gun_mapping_id is not None:
            existing_mapping = DeliveryLocation_Mapping_DispenserUnit.objects.filter(
                dispenser_gun_mapping_id=new_dispenser_gun_mapping_id
            ).exclude(id=instance.id)
            
            if existing_mapping.exists():
                raise serializers.ValidationError("This dispenser gun mapping is already assigned to another delivery location.")

        delivery_location_id = attrs.get('delivery_location_id')
        DU_Accessible_delivery_locations = attrs.get('DU_Accessible_delivery_locations')
        
        final_delivery_location_id = delivery_location_id if delivery_location_id is not None else previous_data['delivery_location_id']
        final_dispenser_gun_mapping_id = new_dispenser_gun_mapping_id if new_dispenser_gun_mapping_id is not None else previous_data['dispenser_gun_mapping_id']
        final_accessible_locations = DU_Accessible_delivery_locations if DU_Accessible_delivery_locations is not None else previous_data['DU_Accessible_delivery_locations']

        if 'Accounts Admin' in roles:
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=final_dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                if not DeliveryLocations.objects.filter(id=final_delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("You can only edit delivery locations that belong to your customer.")
                
                if final_accessible_locations:
                    for location_id in final_accessible_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"Delivery location with ID {location_id} does not belong to your customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")
        
        elif 'IOT Admin' in roles:
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=final_dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                if not DeliveryLocations.objects.filter(id=final_delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("All delivery locations must belong to the same customer as the dispenser gun mapping.")
                
                if final_accessible_locations:
                    for location_id in final_accessible_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"All delivery locations must belong to the same customer. Location ID {location_id} belongs to a different customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")

        attrs['previous_data'] = previous_data
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        previous_data = validated_data.pop('previous_data', {})

        fields_to_update = []
        
        if 'delivery_location_id' in validated_data:
            new_delivery_location_id = validated_data['delivery_location_id']
            if new_delivery_location_id != previous_data['delivery_location_id']:
                instance.delivery_location_id = new_delivery_location_id
                fields_to_update.append('delivery_location_id')

        if 'dispenser_gun_mapping_id' in validated_data:
            new_dispenser_gun_mapping_id = validated_data['dispenser_gun_mapping_id']
            if new_dispenser_gun_mapping_id != previous_data['dispenser_gun_mapping_id']:
                if new_dispenser_gun_mapping_id is not None:
                    dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=new_dispenser_gun_mapping_id)
                    instance.dispenser_gun_mapping_id = dispenser_gun_mapping
                else:
                    instance.dispenser_gun_mapping_id = None
                fields_to_update.append('dispenser_gun_mapping_id')

        if 'DU_Accessible_delivery_locations' in validated_data:
            new_accessible_locations = validated_data['DU_Accessible_delivery_locations']
            if new_accessible_locations != previous_data['DU_Accessible_delivery_locations']:
                instance.DU_Accessible_delivery_locations = new_accessible_locations
                fields_to_update.append('DU_Accessible_delivery_locations')

        if 'remarks' in validated_data:
            new_remarks = validated_data['remarks']
            if new_remarks != previous_data['remarks']:
                instance.remarks = new_remarks
                fields_to_update.append('remarks')

        if fields_to_update:
            instance.updated_by = user.id if user else instance.updated_by
            instance.updated_at = timezone.now()
            fields_to_update.extend(['updated_by', 'updated_at'])
            instance.save(update_fields=fields_to_update)
        else:
            pass

        return instance


class DeleteDeliveryLocationMappingDispenserUnitSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
    def validate(self, attrs):
        instance = self.context.get('instance')
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        roles = self.context.get("roles", [])        
        if 'Accounts Admin' in roles:
            try:
                dispenser_gun_mapping = instance.dispenser_gun_mapping_id
                customer_id = dispenser_gun_mapping.customer                
                if not DeliveryLocations.objects.filter(id=instance.delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("You can only delete delivery location mappings that belong to your customer.")   
            except Exception as e:
                raise serializers.ValidationError("Invalid delivery location mapping data.")
        return attrs
    def delete(self, instance):
        instance.delete()
        return instance

class CreateRequestForFuelDispensingSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    delivery_location_id = serializers.IntegerField(required=False)  
    customer_id = serializers.IntegerField()
    asset_id = serializers.CharField()  
    request_vehicle = serializers.ChoiceField(choices=[0, 1])  
    request_type = serializers.ChoiceField(choices=[0, 1])  
    dispenser_volume = serializers.FloatField(required=False)
    dispenser_price = serializers.FloatField(required=False)
    buffer_reason = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    def validate(self, data):
        user = self.context.get("user")
        login_user_id = getattr(user, "id", None)
        user_id = data.get("user_id")
        delivery_location_id = data.get("delivery_location_id")
        customer_id = data.get("customer_id")
        asset_id = data.get("asset_id")
        request_vehicle = data.get("request_vehicle")
        request_type = data.get("request_type")
        dispenser_volume = data.get("dispenser_volume")
        dispenser_price = data.get("dispenser_price")
        buffer_reason = data.get("buffer_reason")

        try:
            user_obj = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            raise serializers.ValidationError("Invalid user_id")

        if login_user_id != user_id:
            raise serializers.ValidationError("Logged-in user does not match given user_id")

        data["user_name"] = user_obj.name
        data["user_email"] = user_obj.email
        data["user_phone"] = user_obj.mobile
        data["request_vehicle"] = request_vehicle

        if request_vehicle == 1:
            try:
                vin_obj = VIN_Vehicle.objects.filter(vin=asset_id, status=False).latest("created_at")
            except VIN_Vehicle.DoesNotExist:
                raise serializers.ValidationError("No active VIN found with this number or VIN already used.")

            vin_poc_ids = vin_obj.point_of_contact_id or []
            if vin_poc_ids: 
                if user_id not in vin_poc_ids:
                    raise serializers.ValidationError(
                        "You are not authorized to create a fuel dispensing request for this VIN."
                    )
            vin_delivery_locations = vin_obj.delivery_location_id or []
            if not vin_delivery_locations:
                raise serializers.ValidationError("VIN has no linked delivery locations.")
            
            primary_delivery_location_id = vin_delivery_locations[0]
            data["delivery_location_id"] = primary_delivery_location_id
            data["DU_Accessible_delivery_locations"] = vin_delivery_locations
            data["transaction_id"] = vin_obj.transaction_id

            existing_request = RequestFuelDispensingDetails.objects.filter(
                transaction_id=vin_obj.transaction_id,
                ).first()

            if existing_request:
                raise serializers.ValidationError(
                    "This VIN is already assigned for dispensing. Please wait until the current request is completed."
                )
            data["asset_id"] = vin_obj.id
            data["asset_name"] = vin_obj.vin
            data["asset_tag_id"] = ""
            data["asset_tag_type"] = ""
            data["asset_type"] = vin_obj.vehicle_type_name
            if vin_obj.customer_id != customer_id:
                raise serializers.ValidationError("VIN does not belong to the provided customer_id.")
            try:
                customer = Customers.objects.get(id=vin_obj.customer_id)
                data["customer_name"] = customer.name
                data["customer_email"] = customer.email
                data["customer_phone"] = customer.mobile
            except Customers.DoesNotExist:
                raise serializers.ValidationError("Customer linked to VIN not found.")

            mapping = None
            primary_delivery_location_id = None
            for loc_id in vin_delivery_locations:
                mapping = DeliveryLocation_Mapping_DispenserUnit.objects.filter(
                    Q(delivery_location_id=loc_id) |
                    Q(DU_Accessible_delivery_locations__contains=[loc_id])
                ).first()
                if mapping:
                    primary_delivery_location_id = loc_id 
                    break

            if not mapping:
                raise serializers.ValidationError(
                    "No dispenser mapping found for the VIN’s delivery locations (including DU_Accessible list)."
                )
            data["delivery_location_id"] = primary_delivery_location_id
            data["DU_Accessible_delivery_locations"] = vin_delivery_locations
            dispenser_map_id = mapping.dispenser_gun_mapping_id.id
            data["dispenser_gun_mapping_id"] = dispenser_map_id
            try:
                location = DeliveryLocations.objects.get(id=primary_delivery_location_id)
            except DeliveryLocations.DoesNotExist:
                raise serializers.ValidationError("Selected delivery location for VIN not found.")

            data["delivery_location_name"] = location.name

            try:
                dispenser = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_map_id)
                dispenser_unit = DispenserUnits.objects.get(id=dispenser.dispenser_unit.id)
            except Exception:
                raise serializers.ValidationError("Invalid dispenser or unit configuration for VIN location.")

            data["dispenser_serialnumber"] = dispenser_unit.serial_number
            data["dispenser_imeinumber"] = dispenser_unit.imei_number

            if dispenser_volume is None:
                raise serializers.ValidationError("dispenser_volume is required for VIN-based requests.")
            if dispenser_price:
                raise serializers.ValidationError("dispenser_price is not applicable for VIN-based requests.")
            if vin_obj.dispense_volume is None:
                raise serializers.ValidationError("VIN dispense_volume not configured.")

            if dispenser_volume > vin_obj.dispense_volume:
                if not buffer_reason:
                    raise serializers.ValidationError("buffer_reason is required since requested volume exceeds VIN’s limit.")
                data["buffer_dispense_volume"] = dispenser_volume - vin_obj.dispense_volume
                data["buffer_reason"] = buffer_reason
            else:
                data["buffer_dispense_volume"] = 0.0
                data["buffer_reason"] = ""

            if request_type != 0:
                raise serializers.ValidationError("VIN-based requests must be of type Volume (request_type=0).")

            data["dispenser_volume"] = dispenser_volume
            data["dispenser_price"] = 0.0            
        else:
            try:
                mapping = DeliveryLocation_Mapping_DispenserUnit.objects.get(delivery_location_id=delivery_location_id)
            except DeliveryLocation_Mapping_DispenserUnit.DoesNotExist:
                raise serializers.ValidationError("Invalid delivery_location_id")

            dispenser_map_id = mapping.dispenser_gun_mapping_id.id
            data["dispenser_gun_mapping_id"] = dispenser_map_id
            data["DU_Accessible_delivery_locations"] = mapping.DU_Accessible_delivery_locations

            try:
                location = DeliveryLocations.objects.get(id=delivery_location_id)
            except DeliveryLocations.DoesNotExist:
                raise serializers.ValidationError("Delivery Location not found")

            data["delivery_location_name"] = location.name

            if location.customer_id != customer_id:
                raise serializers.ValidationError("Provided customer_id does not match delivery location’s customer.")

            try:
                customer = Customers.objects.get(id=customer_id)
            except Customers.DoesNotExist:
                raise serializers.ValidationError("Customer not found")

            data["customer_name"] = customer.name
            data["customer_email"] = customer.email
            data["customer_phone"] = customer.mobile
            try:
                dispenser = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_map_id)
                dispenser_unit = DispenserUnits.objects.get(id=dispenser.dispenser_unit.id)
            except Exception:
                raise serializers.ValidationError("Invalid dispenser or unit configuration.")

            data["dispenser_serialnumber"] = dispenser_unit.serial_number
            data["dispenser_imeinumber"] = dispenser_unit.imei_number

            try:
                asset = Assets.objects.get(id=int(asset_id))
            except (Assets.DoesNotExist, ValueError):
                raise serializers.ValidationError("Invalid asset_id")

            if asset.customer_id != customer_id:
                raise serializers.ValidationError("Asset does not belong to the given customer")

            accessible_locations = [delivery_location_id] + data["DU_Accessible_delivery_locations"]
            if not DeliveryLocationAssets.objects.filter(
                delivery_location__in=accessible_locations,
                asset_id=asset.id
            ).exists():
                raise serializers.ValidationError("This asset is not accessible to the given delivery location or accessible locations.")

            data["asset_id"] = asset.id
            data["asset_name"] = asset.name
            data["asset_tag_id"] = asset.tag_id
            data["asset_tag_type"] = asset.tag_type
            data["asset_type"] = asset.type

            while True:
                txn_id = "TXN" + str(random.randint(100000000000, 999999999999))
                if not RequestFuelDispensingDetails.objects.filter(transaction_id=txn_id).exists():
                    break
            data["transaction_id"] = txn_id

            if request_type == 0:
                if dispenser_volume is None:
                    raise serializers.ValidationError("dispenser_volume is required for Volume type requests.")
                data["dispenser_volume"] = dispenser_volume
                data["dispenser_price"] = 0.0
            else:
                if dispenser_price is None:
                    raise serializers.ValidationError("dispenser_price is required for Amount type requests.")
                data["dispenser_price"] = dispenser_price
                data["dispenser_volume"] = 0.0

        return data

    def create(self, validated_data):
        remarks = validated_data.get("remarks", "")
        request_vehicle = validated_data.get("request_vehicle")

        RequestFuelDispensingDetails.objects.create(
            user_id=validated_data["user_id"],
            user_name=validated_data["user_name"],
            user_email=validated_data["user_email"],
            user_phone=validated_data["user_phone"],
            dispenser_gun_mapping_id=validated_data["dispenser_gun_mapping_id"],
            dispenser_serialnumber=validated_data["dispenser_serialnumber"],
            dispenser_imeinumber=validated_data["dispenser_imeinumber"],
            delivery_location_id=validated_data["delivery_location_id"],
            delivery_location_name=validated_data["delivery_location_name"],
            DU_Accessible_delivery_locations=validated_data["DU_Accessible_delivery_locations"],
            customer_id=validated_data["customer_id"],
            customer_name=validated_data["customer_name"],
            customer_email=validated_data["customer_email"],
            customer_phone=validated_data["customer_phone"],
            asset_id=validated_data["asset_id"],
            asset_name=validated_data["asset_name"],
            asset_tag_id=validated_data.get("asset_tag_id", ""),
            asset_tag_type=validated_data.get("asset_tag_type", ""),
            asset_type=validated_data.get("asset_type", ""),
            transaction_id=validated_data["transaction_id"],
            dispenser_volume=validated_data["dispenser_volume"],
            dispenser_price=validated_data["dispenser_price"],
            dispenser_live_price=0.0,
            request_type=validated_data["request_type"],
            request_vehicle = validated_data["request_vehicle"],
            request_status=0,
            fuel_state=False,
            transaction_log={},
            remarks=remarks,
            request_created_at=timezone.now(),
            request_created_by=validated_data["user_id"],
        )

        if request_vehicle == 1:
            vin_obj = VIN_Vehicle.objects.get(id=validated_data["asset_id"])
            vin_obj.buffer_dispense_volume = validated_data["buffer_dispense_volume"]
            vin_obj.buffer_reason = validated_data["buffer_reason"]
            vin_obj.save(update_fields=["buffer_dispense_volume", "buffer_reason"])

        return validated_data


class GetFuelDispensingRequestsSerializer(serializers.ModelSerializer):
    DU_Accessible_delivery_locations_details = serializers.SerializerMethodField()
    class Meta:
        model = RequestFuelDispensingDetails
        exclude = ['transaction_log']
        depth = 1

    def get_DU_Accessible_delivery_locations_details(self, instance):
        details = []
        if isinstance(instance.DU_Accessible_delivery_locations, list):
            for loc_id in instance.DU_Accessible_delivery_locations:
                try:
                    location = DeliveryLocations.objects.get(id=loc_id)
                    details.append({
                        "id": location.id,
                        "name": location.name
                    })
                except DeliveryLocations.DoesNotExist:
                    details.append({
                        "id": loc_id,
                        "name": f"Unknown Location (ID: {loc_id})"
                    })
        return details


class GetFuelDispensingRequestsSerializerWithTransactionLog(serializers.ModelSerializer):
    DU_Accessible_delivery_locations_details = serializers.SerializerMethodField()

    class Meta:
        model = RequestFuelDispensingDetails
        fields = '__all__'
        depth = 1

    def get_DU_Accessible_delivery_locations_details(self, instance):
        details = []
        if isinstance(instance.DU_Accessible_delivery_locations, list):
            for loc_id in instance.DU_Accessible_delivery_locations:
                try:
                    location = DeliveryLocations.objects.get(id=loc_id)
                    details.append({
                        "id": location.id,
                        "name": location.name
                    })
                except DeliveryLocations.DoesNotExist:
                    details.append({
                        "id": loc_id,
                        "name": f"Unknown Location (ID: {loc_id})"
                    })
        return details



class AddVINVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIN_Vehicle
        fields = [
            "vin",
            "customer_id",
            "delivery_location_id",
            "point_of_contact_id",
            "vehicle_type",
            "capacity",
            "dg_kv",
            "dispense_volume",
        ]

    def validate(self, data):
        user = self.context["user"]
        roles = self.context["roles"]

        vin = data.get("vin")
        customer_id = data.get("customer_id")
        delivery_location_ids = data.get("delivery_location_id", [])
        point_of_contact_ids = data.get("point_of_contact_id", [])
        vehicle_type_id = data.get("vehicle_type")
        capacity = data.get("capacity")
        dg_kv = data.get("dg_kv")
        existing_vin = (
    VIN_Vehicle.objects
    .filter(vin=vin)
    .order_by('-id')   
    .only('id', 'status')                      
    .first()
)
        if existing_vin:
            if existing_vin.status is False:
                raise serializers.ValidationError("VIN number already exists. Please edit the existing VIN.")

        if 'IOT Admin' not in roles:
            try:
                poc = PointOfContacts.objects.get(user_id=user.id, belong_to_type="customer")
            except PointOfContacts.DoesNotExist:
                raise serializers.ValidationError("You are not associated with any customer.")
            if poc.belong_to_id != customer_id:
                raise serializers.ValidationError("Customer ID mismatch with your association.")


        if delivery_location_ids:
            delivery_location_ids = list(set(delivery_location_ids))  # de-dup
            invalid_ids = []
            owners = set()

            for dl_id in delivery_location_ids:
                qs = (
                    DeliveryLocation_Mapping_DispenserUnit.objects
                    .filter(
                        Q(delivery_location_id=dl_id) |
                        Q(DU_Accessible_delivery_locations__contains=[dl_id])
                    )
                    .select_related("dispenser_gun_mapping_id")
                    .only(
                        "delivery_location_id",
                        "DU_Accessible_delivery_locations",
                        "dispenser_gun_mapping_id",
                    )
                )

                if not qs.exists():
                    invalid_ids.append(dl_id)
                    continue
                for m in qs:
                    cust = getattr(m.dispenser_gun_mapping_id, "customer_id", None)
                    if cust is not None:
                        owners.add(int(cust))

            if invalid_ids:
                raise serializers.ValidationError(
                    f"Invalid delivery_location_id(s) (not present in mapping): {invalid_ids}"
                )

            if len(owners) > 1:
                raise serializers.ValidationError(
                    "All delivery locations must belong to the same customer."
                )

        if point_of_contact_ids:
            pocs = PointOfContacts.objects.filter(user_id__in=point_of_contact_ids,belong_to_type="customer")
            if not pocs.exists():
                raise serializers.ValidationError("One or more Point of Contact IDs are invalid.")

            if 'IOT Admin' not in roles:
                for p in pocs:
                    if p.belong_to_id != customer_id:
                        raise serializers.ValidationError(
                            f"POC {p.id} does not belong to the same customer."
                        )
            else:
                unique_custs = set(p.belong_to_id for p in pocs)
                if len(unique_custs) > 1:
                    raise serializers.ValidationError("All POCs must belong to the same customer.")

        try:
            asset_type = AssetTypes.objects.get(id=vehicle_type_id)
        except AssetTypes.DoesNotExist:
            raise serializers.ValidationError("Invalid vehicle_type ID. Not found in AssetsType table.")

        data["vehicle_type_name"] = asset_type.type

        if not capacity:
            raise serializers.ValidationError("Capacity is mandatory.")

        if data["vehicle_type_name"].lower() == "diesel generator" and not dg_kv:
            raise serializers.ValidationError("DG KV is mandatory for Diesel Generator type.")
        return data

    def create(self, validated_data):
        user = self.context["user"]
        with transaction.atomic():
            while True:
                transaction_id = "VIN" + str(random.randint(100000000000, 999999999999))
                if not RequestFuelDispensingDetails.objects.filter(transaction_id=transaction_id).exists():
                    break
            vin_vehicle = VIN_Vehicle.objects.create(
                vin=validated_data["vin"],
                customer_id=validated_data["customer_id"],
                delivery_location_id=validated_data.get("delivery_location_id", []),
                point_of_contact_id=validated_data.get("point_of_contact_id", []),
                vehicle_type=validated_data["vehicle_type"],
                vehicle_type_name=validated_data["vehicle_type_name"],
                capacity=validated_data["capacity"],
                dg_kv=validated_data.get("dg_kv"),
                dispense_volume=validated_data.get("dispense_volume"),
                transaction_id=transaction_id,
                status=False,
                created_by=user.id,
                created_at=timezone.now(),
            )
        return vin_vehicle


class GetVINVehicleSerializer(serializers.ModelSerializer):
    delivery_location_details = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = VIN_Vehicle
        fields = "__all__"
    def get_delivery_location_details(self, obj):
        details = []
        if isinstance(obj.delivery_location_id, list):
            for loc_id in obj.delivery_location_id:
                try:
                    loc = DeliveryLocations.objects.get(id=loc_id)
                    details.append({
                        "id": loc.id,
                        "name": loc.name
                    })
                except DeliveryLocations.DoesNotExist:
                    details.append({
                        "id": loc_id,
                        "name": f"Unknown Location (ID: {loc_id})"
                    })
        return details

    def get_user_details(self, obj):
        details = []
        if isinstance(obj.point_of_contact_id, list):
            for poc_id in obj.point_of_contact_id:
                try:
                    poc = Users.objects.get(id=poc_id)
                    details.append({
                        "id": poc.id,
                        "name": getattr(poc, "name", f"POC-{poc_id}")
                    })
                except Users.DoesNotExist:
                    details.append({
                        "id": poc_id,
                        "name": f"Unknown User (ID: {poc_id})"
                    })
        return details


class EditVINVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIN_Vehicle
        fields = [
            "delivery_location_id",
            "point_of_contact_id",
            "vehicle_type",
            "capacity",
            "dg_kv",
            "customer_id",
        ]

    def validate(self, data):
        user = self.context["user"]
        roles = self.context["roles"]
        vin_vehicle = self.context["vin_vehicle"]

        if vin_vehicle.status is True:
            raise serializers.ValidationError(
                "This VIN record is locked and cannot be edited as it is already used."
            )

        user_id = user.id

        if "IOT Admin" in roles:
            pass

        elif "Accounts Admin" in roles:
            try:
                poc = PointOfContacts.objects.get(
                    user_id=user_id, belong_to_type="customer"
                )
            except PointOfContacts.DoesNotExist:
                raise serializers.ValidationError("You are not associated with any customer.")
            if poc.belong_to_id != vin_vehicle.customer_id:
                raise serializers.ValidationError(
                    "You are not authorized to edit this VIN vehicle."
                )

        elif any(role in roles for role in ["Dispenser Manager", "Location Manager"]):
            user_pocs = PointOfContacts.objects.filter(
                user_id=user_id, belong_to_type="delivery_location"
            )
            if not user_pocs.exists():
                raise serializers.ValidationError("You are not associated with any delivery location.")

            delivery_location_ids = [poc.belong_to_id for poc in user_pocs]
            vin_locations = vin_vehicle.delivery_location_id or []

            if not any(loc_id in vin_locations for loc_id in delivery_location_ids):
                raise serializers.ValidationError(
                    "You are not authorized to edit this VIN vehicle."
                )
        else:
            raise serializers.ValidationError(
                "You are not authorized to edit VIN vehicles."
            )

        if "vehicle_type" in data:
            try:
                asset_type = AssetTypes.objects.get(id=data["vehicle_type"])
                data["vehicle_type_name"] = asset_type.type
            except AssetTypes.DoesNotExist:
                raise serializers.ValidationError("Invalid vehicle_type ID. Not found in AssetTypes table.")

        if "capacity" in data and not data["capacity"]:
            raise serializers.ValidationError("Capacity cannot be empty.")

        vehicle_type_name = (
            data.get("vehicle_type_name") or vin_vehicle.vehicle_type_name
        )
        if vehicle_type_name and vehicle_type_name.lower() == "diesel generator":
            if "dg_kv" not in data or not data["dg_kv"]:
                raise serializers.ValidationError("DG KV is mandatory for Diesel Generator type.")

        return data

    def update(self, instance, validated_data):
        user = self.context["user"]

        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.updated_by = user.id
            instance.updated_at = timezone.now()
            instance.save()
        return instance


class DeleteVINVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIN_Vehicle
        fields = ["id"]

    def validate(self, data):
        user = self.context["user"]
        roles = self.context["roles"]
        vin_vehicle = self.context["vin_vehicle"]

        if vin_vehicle.status is True:
            raise serializers.ValidationError("This VIN record cannot be deleted as it has already been used.")

        user_id = user.id

        if "IOT Admin" in roles:
            pass 

        elif "Accounts Admin" in roles:
            try:
                poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
            except PointOfContacts.DoesNotExist:
                raise serializers.ValidationError("You are not associated with any customer.")
            if poc.belong_to_id != vin_vehicle.customer_id:
                raise serializers.ValidationError("You are not authorized to delete this VIN vehicle.")

        elif any(role in roles for role in ["Dispenser Manager", "Location Manager"]):
            user_pocs = PointOfContacts.objects.filter(user_id=user_id, belong_to_type="delivery_location")
            if not user_pocs.exists():
                raise serializers.ValidationError("You are not associated with any delivery location.")
            delivery_location_ids = [poc.belong_to_id for poc in user_pocs]
            vin_locations = vin_vehicle.delivery_location_id or []
            if not any(loc_id in vin_locations for loc_id in delivery_location_ids):
                raise serializers.ValidationError("You are not authorized to delete this VIN vehicle.")
        else:
            raise serializers.ValidationError("You are not authorized to delete VIN vehicles.")
        return data

    def delete(self, instance):
        instance.delete()
        return instance



class CreateDispenserGunMappingToVehiclesSerializer(serializers.ModelSerializer):
    vehicle = serializers.IntegerField(required=True)
    dispenser_unit = serializers.PrimaryKeyRelatedField(
        queryset=DispenserUnits.objects.all(),
        required=True
    )
    gun_unit = serializers.PrimaryKeyRelatedField(
        queryset=GunUnits.objects.all(),
        required=False,
        allow_null=True
    )
    totalizer_reading = serializers.FloatField(required=True)
    total_reading_amount = serializers.FloatField(required=True)
    live_price = serializers.FloatField(required=True)
    grade = serializers.IntegerField(required=True)
    nozzle = serializers.IntegerField(required=True)
    dispenser_position = serializers.IntegerField(required=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor = serializers.BooleanField(required=False, default=False)
    fuel_level_sensor_type = serializers.IntegerField(required=False, allow_null=True)
    fuel_level_sensor_brand = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_configuration = serializers.JSONField(required=False, allow_null=True)
    tank_capacity = serializers.FloatField(required=False, allow_null=True)
    class Meta:
        model = Dispenser_Gun_Mapping_To_Vehicles
        fields = [
            'vehicle',
            'dispenser_unit',
            'gun_unit',
            'totalizer_reading',
            'total_reading_amount',
            'live_price',
            'grade',
            'nozzle',
            'installation_mode',
            'dispenser_position',
            'remarks',
            'fuel_level_sensor',
            'fuel_level_sensor_type',
            'fuel_level_sensor_brand',
            'fuel_level_sensor_description',
            'fuel_level_sensor_configuration',
            'tank_capacity',
        ]

    def validate_vehicle(self, value):
        if not Vehicles.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Vehicle does not exist.")
        return value

    def validate(self, attrs):
        dispenser_unit = attrs.get('dispenser_unit')
        gun_unit = attrs.get('gun_unit')

        if dispenser_unit and dispenser_unit.assigned_status:
            raise serializers.ValidationError(
                "This dispenser unit is already assigned and cannot be allotted."
            )
        if gun_unit and gun_unit.assigned_status:
            raise serializers.ValidationError(
                "This gun unit is already assigned and cannot be allotted."
            )
        

        fuel_level_sensor = attrs.get('fuel_level_sensor', False)

        fuel_fields = [
            attrs.get('fuel_level_sensor_type'),
            attrs.get('fuel_level_sensor_brand'),
            attrs.get('fuel_level_sensor_description'),
            attrs.get('fuel_level_sensor_configuration'),
        ]

        fuel_data_provided = any(v not in [None, '', {}] for v in fuel_fields)

        if fuel_data_provided and not fuel_level_sensor:
            raise serializers.ValidationError({
                "fuel_level_sensor": (
                    "fuel_level_sensor must be enabled to provide fuel sensor details."
                )
            })


        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user", None)

        dispenser_unit = validated_data['dispenser_unit']
        gun_unit = validated_data.get('gun_unit')  

        if DispenserUnits.objects.select_for_update().get(
            pk=dispenser_unit.pk
        ).assigned_status:
            raise serializers.ValidationError(
                "This dispenser unit is already assigned and cannot be allotted."
            )

        if gun_unit:
            if GunUnits.objects.select_for_update().get(
                pk=gun_unit.pk
            ).assigned_status:
                raise serializers.ValidationError(
                    "This gun unit is already assigned and cannot be allotted."
                )

        instance = Dispenser_Gun_Mapping_To_Vehicles.objects.create(
            vehicle=validated_data['vehicle'],
            dispenser_unit=dispenser_unit,
            gun_unit=gun_unit, 
            totalizer_reading=validated_data['totalizer_reading'],
            total_reading_amount=validated_data['total_reading_amount'],
            installation_mode=validated_data['installation_mode'],
            live_price=validated_data['live_price'],
            grade=validated_data['grade'],
            nozzle=validated_data['nozzle'],
            dispenser_position=validated_data['dispenser_position'],
            remarks=validated_data.get('remarks'),
            tank_capacity=validated_data.get('tank_capacity'),
            fuel_level_sensor=validated_data.get('fuel_level_sensor', False),
            fuel_level_sensor_type=validated_data.get('fuel_level_sensor_type'),
            fuel_level_sensor_brand=validated_data.get('fuel_level_sensor_brand'),
            fuel_level_sensor_description=validated_data.get('fuel_level_sensor_description'),
            fuel_level_sensor_configuration=validated_data.get('fuel_level_sensor_configuration'),

            created_by=user.id if user else None,
            created_at=timezone.now(),
        )

        dispenser_unit.assigned_status = True
        dispenser_unit.updated_by = user.id if user else dispenser_unit.updated_by
        dispenser_unit.updated_at = timezone.now()
        dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

        if gun_unit:
            gun_unit.assigned_status = True
            gun_unit.updated_by = user.id if user else gun_unit.updated_by
            gun_unit.updated_at = timezone.now()
            gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        return instance



class GetDispenserGunMappingToVehiclesSerializer(serializers.ModelSerializer):
    dispenser_unit = GetDispenserUnitsSerializer()
    gun_unit = GetGunUnitsSerializer()
    last_fuel_reading = serializers.SerializerMethodField()

    class Meta:
        model = Dispenser_Gun_Mapping_To_Vehicles
        fields = '__all__'
        depth = 1

    def get_last_fuel_reading(self, obj):
        last = FuelSensorReadings.objects.filter(
            dispenser_customer_mapping=obj
        ).order_by("-epoch_time").first()

        if not last:
            return {
                "fuel_level": None,
                "temperature": None,
                "epoch_time": None,
                "data_type": None,
                "transaction_id": None
            }
        return LastFuelSensorReadingSerializer(last).data

class VehicleNoSerializer(serializers.Serializer):
    vehicle_no = serializers.CharField(required=True)


class EditDispenserGunMappingToVehiclesSerializer(serializers.ModelSerializer):
    dispenser_unit = serializers.PrimaryKeyRelatedField(
        queryset=DispenserUnits.objects.all(),
        required=False
    )
    gun_unit = serializers.PrimaryKeyRelatedField(
        queryset=GunUnits.objects.all(),
        required=False,
        allow_null=True
    )

    totalizer_reading = serializers.FloatField(required=False)
    total_reading_amount = serializers.FloatField(required=False)
    live_price = serializers.FloatField(required=False)
    grade = serializers.IntegerField(required=False)
    nozzle = serializers.IntegerField(required=False)
    installation_mode = serializers.IntegerField(required=False)
    dispenser_position = serializers.IntegerField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tank_capacity = serializers.FloatField(required=False, allow_null=True)
    fuel_level_sensor = serializers.BooleanField(required=False)
    fuel_level_sensor_type = serializers.IntegerField(required=False, allow_null=True)
    fuel_level_sensor_brand = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fuel_level_sensor_configuration = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Dispenser_Gun_Mapping_To_Vehicles
        fields = [
            'dispenser_unit',
            'gun_unit',
            'totalizer_reading',
            'total_reading_amount',
            'live_price',
            'grade',
            'dispenser_position',
            'installation_mode',
            'nozzle',
            'remarks',
            'tank_capacity',
            'fuel_level_sensor',
            'fuel_level_sensor_type',
            'fuel_level_sensor_brand',
            'fuel_level_sensor_description',
            'fuel_level_sensor_configuration',
        ]

    def validate(self, attrs):
        instance = self.instance
        if not instance:
            raise serializers.ValidationError("Instance not found.")

        fuel_sensor = attrs.get('fuel_level_sensor', instance.fuel_level_sensor)

        fuel_fields = [
            attrs.get('fuel_level_sensor_type', instance.fuel_level_sensor_type),
            attrs.get('fuel_level_sensor_brand', instance.fuel_level_sensor_brand),
            attrs.get('fuel_level_sensor_description', instance.fuel_level_sensor_description),
            attrs.get('fuel_level_sensor_configuration', instance.fuel_level_sensor_configuration),
        ]

        fuel_data_provided = any(v not in [None, '', {}] for v in fuel_fields)

        if fuel_data_provided and not fuel_sensor:
            raise serializers.ValidationError({
                "fuel_level_sensor": (
                    "fuel_level_sensor must be enabled to provide fuel sensor details."
                )
            })

        new_dispenser = attrs.get('dispenser_unit', serializers.empty)
        if new_dispenser is not serializers.empty and new_dispenser != instance.dispenser_unit:
            if new_dispenser.assigned_status:
                raise serializers.ValidationError(
                    "This dispenser unit is already assigned and cannot be allotted."
                )

            attrs['_new_dispenser_unit'] = new_dispenser
            attrs['_previous_dispenser_unit'] = instance.dispenser_unit

        new_gun = attrs.get('gun_unit', serializers.empty)
        if new_gun is not serializers.empty and new_gun != instance.gun_unit:
            if new_gun is not None and new_gun.assigned_status:
                raise serializers.ValidationError(
                    "This gun unit is already assigned and cannot be allotted."
                )

            attrs['_new_gun_unit'] = new_gun
            attrs['_previous_gun_unit'] = instance.gun_unit

        return attrs
    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        for field in [
            'totalizer_reading',
            'total_reading_amount',
            'live_price',
            'grade',
            'dispenser_position',
            'installation_mode',
            'nozzle',
            'remarks',
            'tank_capacity',
        ]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        fuel_level_sensor = validated_data.get(
            'fuel_level_sensor', instance.fuel_level_sensor
        )
        instance.fuel_level_sensor = fuel_level_sensor

        if fuel_level_sensor:
            instance.fuel_level_sensor_type = validated_data.get(
                'fuel_level_sensor_type', instance.fuel_level_sensor_type
            )
            instance.fuel_level_sensor_brand = validated_data.get(
                'fuel_level_sensor_brand', instance.fuel_level_sensor_brand
            )
            instance.fuel_level_sensor_description = validated_data.get(
                'fuel_level_sensor_description', instance.fuel_level_sensor_description
            )
            instance.fuel_level_sensor_configuration = validated_data.get(
                'fuel_level_sensor_configuration', instance.fuel_level_sensor_configuration
            )
        else:
            instance.fuel_level_sensor_type = None
            instance.fuel_level_sensor_brand = None
            instance.fuel_level_sensor_description = None
            instance.fuel_level_sensor_configuration = None

        if '_new_dispenser_unit' in validated_data:
            new_du = DispenserUnits.objects.select_for_update().get(
                pk=validated_data['_new_dispenser_unit'].pk
            )
            prev_du = DispenserUnits.objects.select_for_update().get(
                pk=validated_data['_previous_dispenser_unit'].pk
            )

            if new_du.assigned_status:
                raise serializers.ValidationError(
                    "This dispenser unit is already assigned."
                )

            instance.dispenser_unit = new_du

            new_du.assigned_status = True
            new_du.updated_by = user.id if user else new_du.updated_by
            new_du.updated_at = timezone.now()
            new_du.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

            prev_du.assigned_status = False
            prev_du.updated_by = user.id if user else prev_du.updated_by
            prev_du.updated_at = timezone.now()
            prev_du.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

        if '_new_gun_unit' in validated_data:
            prev_gun = validated_data['_previous_gun_unit']
            new_gun = validated_data['_new_gun_unit']

            if prev_gun:
                prev_gun = GunUnits.objects.select_for_update().get(pk=prev_gun.pk)
                prev_gun.assigned_status = False
                prev_gun.updated_by = user.id if user else prev_gun.updated_by
                prev_gun.updated_at = timezone.now()
                prev_gun.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

            if new_gun:
                new_gun = GunUnits.objects.select_for_update().get(pk=new_gun.pk)
                if new_gun.assigned_status:
                    raise serializers.ValidationError(
                        "This gun unit is already assigned."
                    )

                new_gun.assigned_status = True
                new_gun.updated_by = user.id if user else new_gun.updated_by
                new_gun.updated_at = timezone.now()
                new_gun.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

                instance.gun_unit = new_gun
            else:
                instance.gun_unit = None
        instance.updated_by = user.id if user else instance.updated_by
        instance.updated_at = timezone.now()
        instance.save()

        return instance


class EditStatusAndAssignedStatusOfDispenserGunMappingToVehiclesSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(required=False)
    assigned_status = serializers.BooleanField(required=False)
    
    class Meta:
        model = Dispenser_Gun_Mapping_To_Vehicles
        fields = ['status', 'assigned_status']
        
    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        if 'status' in attrs and 'assigned_status' in attrs:
            raise serializers.ValidationError("Only one field can be updated at a time: either 'status' or 'assigned_status'.")
        
        if 'status' not in attrs and 'assigned_status' not in attrs:
            raise serializers.ValidationError("Either 'status' or 'assigned_status' must be provided.")
        return attrs
        
    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        
        if 'status' in validated_data:
            instance.status = validated_data['status']
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
            
        elif 'assigned_status' in validated_data:
            new_assigned_status = validated_data['assigned_status']
            instance.assigned_status = new_assigned_status
            
            if not new_assigned_status:
                instance.status = False
            
            dispenser_unit = instance.dispenser_unit
            dispenser_unit.assigned_status = new_assigned_status
            dispenser_unit.updated_by = (user.id if user else dispenser_unit.updated_by)
            dispenser_unit.updated_at = timezone.now()
            dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])            
            gun_unit = instance.gun_unit
            if gun_unit:
                gun_unit.assigned_status = new_assigned_status
                gun_unit.updated_by = (user.id if user else gun_unit.updated_by)
                gun_unit.updated_at = timezone.now()
                gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])                
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
        return instance


class DeleteDispenserGunMappingToVehiclesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
    def validate(self, attrs):
        instance = self.context.get('instance')
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        if instance.assigned_status is True:
            raise serializers.ValidationError("Cannot delete dispenser gun mapping that is currently assigned to a vehicles.")
        return attrs
    
    def delete(self, instance):
        instance.delete()
        return instance


class CreateRequestForOrderFuelDispensingSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    route_plan_details_id = serializers.IntegerField()
    dispenser_gun_mapping_id = serializers.IntegerField()
    asset_id = serializers.CharField(required=False)  
    asset_name = serializers.CharField(required=False)
    request_type = serializers.ChoiceField(choices=[0, 1]) 
    dispenser_volume = serializers.FloatField(required=False)
    dispenser_price = serializers.FloatField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True)
    def validate(self, data):
        user = self.context.get("user")
        login_user_id = getattr(user, "id", None)
        user_id = data.get("user_id")
        route_plan_details_id = data.get("route_plan_details_id")
        dispenser_gun_mapping_id = data.get("dispenser_gun_mapping_id")
        asset_id = data.get("asset_id")
        asset_name = data.get("asset_name")
        request_type = data.get("request_type")
        dispenser_volume = data.get("dispenser_volume")
        dispenser_price = data.get("dispenser_price")
        buffer_reason = data.get("buffer_reason")

        try:
            user_obj = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            raise serializers.ValidationError("Invalid user_id")

        if login_user_id != user_id:
            raise serializers.ValidationError("Logged-in user does not match given user_id")

        data["driver_name"] = user_obj.name
        data["driver_email"] = user_obj.email
        data["driver_phone"] = user_obj.mobile

        try:
            route_plan_details = RoutePlanDetails.objects.get(id=route_plan_details_id)
        except RoutePlanDetails.DoesNotExist:
            raise serializers.ValidationError("Invalid route_plan_details_id")

        route_plan_id = route_plan_details.route_plan.id
        data["route_plan_id"] = route_plan_id
        order_id = route_plan_details.subject_id
        data["order_id"] = order_id
        try:
            order_details = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            raise serializers.ValidationError("Invalid order_id")
        customer_id = order_details.customer_id
        try:
            customer = Customers.objects.get(id=customer_id)
        except Customers.DoesNotExist:
            raise serializers.ValidationError("Customer not found")
        data["customer_id"] = customer_id
        data["customer_name"] = customer.name
        data["customer_email"] = customer.email
        data["customer_phone"] = customer.mobile
        existing_request = OrderFuelDispensingDetails.objects.filter(
            order_id=order_id,
            route_plan_details_id=route_plan_details_id,
            request_status__in=[0, 1, 2]
        ).first()

        if existing_request:
            raise serializers.ValidationError(
                "A fuel dispensing transaction is already in progress for this order."
            )
        try:
            route_plan = RoutePlans.objects.get(id=route_plan_id)
        except RoutePlans.DoesNotExist:
            raise serializers.ValidationError("Invalid route_plan_id")
        vehicle_id = route_plan.vehicle_id
        data["vehicle_id"] = vehicle_id

        try:
            mapping = Dispenser_Gun_Mapping_To_Vehicles.objects.get(
                id=dispenser_gun_mapping_id
            )
        except Dispenser_Gun_Mapping_To_Vehicles.DoesNotExist:
            raise serializers.ValidationError("Invalid dispenser_gun_mapping_id")

        dispenser_unit = mapping.dispenser_unit

        if not dispenser_unit:
            raise serializers.ValidationError("Dispenser unit not linked to this mapping")

        data["dispenser_serialnumber"] = dispenser_unit.serial_number
        data["dispenser_imeinumber"] = dispenser_unit.imei_number

        data["dispenser_gun_mapping_id"] = mapping.id
        try:
            delivery_location_id = Orders.objects.get(id=order_id).delivery_location_id
        except:
            raise serializers.ValidationError("Delivery Location not found")
        data["delivery_location_id"] = delivery_location_id
        
        total_ordered_quantity = Orders.objects.get(id=order_id).total_quantity
        data["total_ordered_quantity"] = total_ordered_quantity

        if asset_id:
            try:
                asset = Assets.objects.get(id=int(asset_id))
            except (Assets.DoesNotExist, ValueError):
                raise serializers.ValidationError("Invalid asset_id")

            data["asset_id"] = asset.id
            data["asset_name"] = asset.name
            data["asset_tag_id"] = asset.tag_id
            data["asset_tag_type"] = asset.tag_type
            data["asset_type"] = asset.type

        else:
            if not asset_name:
                raise serializers.ValidationError(
            "asset_name is required when asset_id is not provided"
        )

            data["asset_id"] = None
            data["asset_name"] = asset_name
            data["asset_tag_id"] = None
            data["asset_tag_type"] = None
            data["asset_type"] = None
        while True:
            txn_id = "TXN" + str(random.randint(100000000000, 999999999999))
            if not RequestFuelDispensingDetails.objects.filter(transaction_id=txn_id).exists():
                break
        data["transaction_id"] = txn_id

        if request_type == 0:
            if dispenser_volume is None:
                raise serializers.ValidationError("dispenser_volume is required for Volume type requests.")
            latest_record = OrderFuelDispensingDetails.objects.filter(
                order_id=order_id
            ).order_by("-id").first()

            if latest_record:
                remaining_qty = latest_record.remaining_quantity_dispensed
                if remaining_qty is not None and dispenser_volume > remaining_qty:
                    if not buffer_reason:
                        raise serializers.ValidationError(
                            "Requested volume exceeds remaining order quantity. "
                            "buffer_reason is required for extra quantity."
                        )
            else:
                if total_ordered_quantity is not None and dispenser_volume > total_ordered_quantity:
                    if not buffer_reason:
                        raise serializers.ValidationError(
                            "Requested volume exceeds total ordered quantity. "
                            "buffer_reason is required for extra quantity."
                        )
            data["dispenser_volume"] = dispenser_volume
            data["dispenser_price"] = 0.0
        else:
            if dispenser_price is None:
                raise serializers.ValidationError("dispenser_price is required for Amount type requests.")
            data["dispenser_price"] = dispenser_price
            data["dispenser_volume"] = 0.0
        return data

    def create(self, validated_data):
        remarks = validated_data.get("remarks", "")
        OrderFuelDispensingDetails.objects.create(
            driver_id=validated_data["user_id"],
            driver_name=validated_data["driver_name"],
            driver_email=validated_data["driver_email"],
            driver_phone=validated_data["driver_phone"],
            customer_id=validated_data["customer_id"],
            customer_name=validated_data["customer_name"],
            customer_email=validated_data["customer_email"],
            customer_phone=validated_data["customer_phone"],
            vehicle_id=validated_data["vehicle_id"],
            route_plan_details_id=validated_data["route_plan_details_id"],
            route_plan_id=validated_data["route_plan_id"],
            order_id=validated_data["order_id"],
            total_ordered_quantity=validated_data["total_ordered_quantity"],
            dispenser_gun_mapping_id=validated_data["dispenser_gun_mapping_id"],
            dispenser_serialnumber=validated_data["dispenser_serialnumber"],
            dispenser_imeinumber=validated_data["dispenser_imeinumber"],
            delivery_location_id=validated_data["delivery_location_id"],
            asset_id=validated_data.get("asset_id", None),
            asset_name=validated_data["asset_name"],
            asset_tag_id=validated_data.get("asset_tag_id", ""),
            asset_tag_type=validated_data.get("asset_tag_type", ""),
            asset_type=validated_data.get("asset_type", ""),
            transaction_id=validated_data["transaction_id"],
            dispenser_volume=validated_data["dispenser_volume"],
            dispenser_price=validated_data["dispenser_price"],
            dispenser_live_price=0.0,
            request_type=validated_data["request_type"],
            request_status=0,
            fuel_state=False,
            transaction_log={},
            remarks=remarks,
            buffer_reason=validated_data.get("buffer_reason"),
            request_created_at=timezone.now(),
            request_created_by=validated_data["user_id"],
        )
        return validated_data


class VehicleBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicles
        fields = [
            "id",
            "vehicle_no"
        ]

class GetOrderFuelDispensingDetailswithTransactionLogSerializer(serializers.ModelSerializer):
    vehicle = serializers.SerializerMethodField()

    class Meta:
        model = OrderFuelDispensingDetails
        fields = "__all__"

    def get_vehicle(self, obj):
        if not obj.vehicle_id:
            return None

        vehicle = Vehicles.objects.filter(
            id=obj.vehicle_id,
            deleted_at__isnull=True
        ).first()

        if not vehicle:
            return None
        return VehicleBasicSerializer(vehicle).data

class GetOrderFuelDispensingDetailsSerializer(serializers.ModelSerializer):
    vehicle = serializers.SerializerMethodField()
    class Meta:
        model = OrderFuelDispensingDetails
        exclude = ["transaction_log"]
    def get_vehicle(self, obj):
        if not obj.vehicle_id:
            return None
        vehicle = Vehicles.objects.filter(
            id=obj.vehicle_id,
            deleted_at__isnull=True
        ).first()
        if not vehicle:
            return None
        return VehicleBasicSerializer(vehicle).data

class GetFuelReadingsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelSensorReadings
        fields = '__all__'

