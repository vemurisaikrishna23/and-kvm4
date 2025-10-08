# serializers.py
from rest_framework import serializers
from passlib.hash import bcrypt
from existing_tables.models import *
from .models import *
from django.utils import timezone
from django.db import transaction
import random
import string
from django.utils.crypto import salted_hmac

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

        # bcrypt $2y$... check
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

        # stash instance for the view to use
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
    dispenser_unit = serializers.PrimaryKeyRelatedField(queryset=DispenserUnits.objects.all(), required=True)
    gun_unit = serializers.PrimaryKeyRelatedField(queryset=GunUnits.objects.all(), required=True)
    totalizer_reading = serializers.FloatField(required=True)
    total_reading_amount = serializers.FloatField(required=True)
    live_price = serializers.FloatField(required=True)
    grade = serializers.IntegerField(required=True)
    nozzle = serializers.IntegerField(required=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

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
        ]
        extra_kwargs = {
            'live_totalizer_reading': {'required': False},
            'live_total_reading_amount': {'required': False},
        }

    def validate_customer(self, value):
        if not Customers.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Customer does not exist.")
        return value

    def validate(self, attrs):
        dispenser_unit = attrs.get('dispenser_unit')
        gun_unit = attrs.get('gun_unit')

        # Dispenser unit must be unassigned
        if dispenser_unit and dispenser_unit.assigned_status is True:
            raise serializers.ValidationError("This dispenser unit is already assigned and cannot be allotted.")

        # Gun unit must be unassigned
        if gun_unit and gun_unit.assigned_status is True:
            raise serializers.ValidationError("This gun unit is already assigned and cannot be allotted.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context.get("user", None)

        dispenser_unit = validated_data['dispenser_unit']
        gun_unit = validated_data['gun_unit']

        if DispenserUnits.objects.select_for_update().get(pk=dispenser_unit.pk).assigned_status:
            raise serializers.ValidationError("This dispenser unit is already assigned and cannot be allotted.")
        if GunUnits.objects.select_for_update().get(pk=gun_unit.pk).assigned_status:
            raise serializers.ValidationError("This gun unit is already assigned and cannot be allotted.")

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
            created_by=(user.id if user else None),
            created_at=timezone.now(),
        )

        # Mark units as assigned
        dispenser_unit.assigned_status = True
        dispenser_unit.updated_by = (user.id if user else dispenser_unit.updated_by)
        dispenser_unit.updated_at = timezone.now()
        dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

        gun_unit.assigned_status = True
        gun_unit.updated_by = (user.id if user else gun_unit.updated_by)
        gun_unit.updated_at = timezone.now()
        gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])

        return instance


class GetDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    dispenser_unit = GetDispenserUnitsSerializer()
    gun_unit = GetGunUnitsSerializer()
    # customer = GetCustomersSerializer()
    class Meta:
        model = Dispenser_Gun_Mapping_To_Customer
        fields = '__all__'
        depth = 1





class EditDispenserGunMappingToCustomerSerializer(serializers.ModelSerializer):
    dispenser_unit = serializers.PrimaryKeyRelatedField(queryset=DispenserUnits.objects.all(), required=False)
    gun_unit = serializers.PrimaryKeyRelatedField(queryset=GunUnits.objects.all(), required=False)
    totalizer_reading = serializers.FloatField(required=False)
    total_reading_amount = serializers.FloatField(required=False)
    live_price = serializers.FloatField(required=False)
    grade = serializers.IntegerField(required=False)
    nozzle = serializers.IntegerField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)

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
        ]

    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        # Get previous data
        previous_data = {
            'dispenser_unit': instance.dispenser_unit,
            'gun_unit': instance.gun_unit,
            'totalizer_reading': instance.totalizer_reading,
            'total_reading_amount': instance.total_reading_amount,
            'live_price': instance.live_price,
            'grade': instance.grade,
            'nozzle': instance.nozzle,
            'remarks': instance.remarks,
        }

        # Check if dispenser_unit is being changed
        new_dispenser_unit = attrs.get('dispenser_unit')
        if new_dispenser_unit and new_dispenser_unit != previous_data['dispenser_unit']:
            # Validate new dispenser unit exists and is not assigned
            if new_dispenser_unit.assigned_status is True:
                raise serializers.ValidationError("This dispenser unit is already assigned and cannot be allotted.")
            
            # Store for later processing
            attrs['_new_dispenser_unit'] = new_dispenser_unit
            attrs['_previous_dispenser_unit'] = previous_data['dispenser_unit']

        # Check if gun_unit is being changed
        new_gun_unit = attrs.get('gun_unit')
        if new_gun_unit and new_gun_unit != previous_data['gun_unit']:
            # Validate new gun unit exists and is not assigned
            if new_gun_unit.assigned_status is True:
                raise serializers.ValidationError("This gun unit is already assigned and cannot be allotted.")
            
            # Store for later processing
            attrs['_new_gun_unit'] = new_gun_unit
            attrs['_previous_gun_unit'] = previous_data['gun_unit']

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        
        # Get previous data for comparison
        previous_data = {
            'dispenser_unit': instance.dispenser_unit,
            'gun_unit': instance.gun_unit,
            'totalizer_reading': instance.totalizer_reading,
            'total_reading_amount': instance.total_reading_amount,
            'live_price': instance.live_price,
            'grade': instance.grade,
            'nozzle': instance.nozzle,
            'remarks': instance.remarks,
        }

        # Update fields only if they are provided in the payload
        # If not provided, keep the previous data
        instance.totalizer_reading = validated_data.get('totalizer_reading', previous_data['totalizer_reading'])
        instance.total_reading_amount = validated_data.get('total_reading_amount', previous_data['total_reading_amount'])
        instance.live_price = validated_data.get('live_price', previous_data['live_price'])
        instance.grade = validated_data.get('grade', previous_data['grade'])
        instance.nozzle = validated_data.get('nozzle', previous_data['nozzle'])
        instance.remarks = validated_data.get('remarks', previous_data['remarks'])
        
        # Handle dispenser_unit change
        if '_new_dispenser_unit' in validated_data:
            new_dispenser_unit = validated_data['_new_dispenser_unit']
            previous_dispenser_unit = validated_data['_previous_dispenser_unit']
            
            # Update the instance
            instance.dispenser_unit = new_dispenser_unit
            
            # Mark new dispenser unit as assigned
            new_dispenser_unit.assigned_status = True
            new_dispenser_unit.updated_by = (user.id if user else new_dispenser_unit.updated_by)
            new_dispenser_unit.updated_at = timezone.now()
            new_dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            # Mark previous dispenser unit as unassigned
            previous_dispenser_unit.assigned_status = False
            previous_dispenser_unit.updated_by = (user.id if user else previous_dispenser_unit.updated_by)
            previous_dispenser_unit.updated_at = timezone.now()
            previous_dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        else:
            # Keep the same dispenser unit
            instance.dispenser_unit = previous_data['dispenser_unit']

        # Handle gun_unit change
        if '_new_gun_unit' in validated_data:
            new_gun_unit = validated_data['_new_gun_unit']
            previous_gun_unit = validated_data['_previous_gun_unit']
            
            # Update the instance
            instance.gun_unit = new_gun_unit
            
            # Mark new gun unit as assigned
            new_gun_unit.assigned_status = True
            new_gun_unit.updated_by = (user.id if user else new_gun_unit.updated_by)
            new_gun_unit.updated_at = timezone.now()
            new_gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            # Mark previous gun unit as unassigned
            previous_gun_unit.assigned_status = False
            previous_gun_unit.updated_by = (user.id if user else previous_gun_unit.updated_by)
            previous_gun_unit.updated_at = timezone.now()
            previous_gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        else:
            # Keep the same gun unit
            instance.gun_unit = previous_data['gun_unit']

        # Update the mapping instance
        instance.updated_by = (user.id if user else instance.updated_by)
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
        
        # Check if both fields are provided
        if 'status' in attrs and 'assigned_status' in attrs:
            raise serializers.ValidationError("Only one field can be updated at a time: either 'status' or 'assigned_status'.")
        
        # Check if no fields are provided
        if 'status' not in attrs and 'assigned_status' not in attrs:
            raise serializers.ValidationError("Either 'status' or 'assigned_status' must be provided.")
            
        return attrs
        
    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        
        # Update status field only
        if 'status' in validated_data:
            instance.status = validated_data['status']
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
            
        # Update assigned_status field and related unit statuses
        elif 'assigned_status' in validated_data:
            new_assigned_status = validated_data['assigned_status']
            instance.assigned_status = new_assigned_status
            
            # If assigned_status is being disabled, also disable the status field
            if not new_assigned_status:
                instance.status = False
            
            # Update dispenser unit assigned_status
            dispenser_unit = instance.dispenser_unit
            dispenser_unit.assigned_status = new_assigned_status
            dispenser_unit.updated_by = (user.id if user else dispenser_unit.updated_by)
            dispenser_unit.updated_at = timezone.now()
            dispenser_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            # Update gun unit assigned_status
            gun_unit = instance.gun_unit
            gun_unit.assigned_status = new_assigned_status
            gun_unit.updated_by = (user.id if user else gun_unit.updated_by)
            gun_unit.updated_at = timezone.now()
            gun_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            # Update the mapping instance
            instance.updated_by = (user.id if user else instance.updated_by)
            instance.updated_at = timezone.now()
            instance.save()
        
        return instance


class DeleteDispenserGunMappingToCustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
    def validate(self, attrs):
        instance = self.context.get('instance')  # Changed from getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        # Check if assigned_status is True
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
        
        # Check if node unit is already assigned to any customer
        if NodeDispenserCustomerMapping.objects.filter(node_unit=node_unit).exists():
            raise serializers.ValidationError("Node unit already assigned to a customer.")
        
        # If dispenser_unit is provided, check if it's assigned to the same customer
        if dispenser_unit:
            # Check if this dispenser unit is assigned to this specific customer
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
        
        # Double-check node unit is not assigned (race condition protection)
        if NodeUnits.objects.select_for_update().get(pk=node_unit.pk).assigned_status:
            raise serializers.ValidationError("This node unit is already assigned and cannot be allotted.")
        
        # Double-check dispenser unit is not assigned to another node unit (if provided)
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
        
        # Mark node unit as assigned
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
        
        # Get previous data
        previous_data = {
            'node_unit': instance.node_unit,
            'dispenser_unit': instance.dispenser_unit,
            'fuel_sensor_type': instance.fuel_sensor_type,
            'remarks': instance.remarks,
        }

        # Check if node_unit is being changed
        new_node_unit = attrs.get('node_unit')
        if new_node_unit and new_node_unit != previous_data['node_unit']:
            # Check if new node unit is already assigned to any customer
            if NodeDispenserCustomerMapping.objects.filter(node_unit=new_node_unit).exclude(id=instance.id).exists():
                raise serializers.ValidationError("This node unit is already assigned to another customer.")
            
            # Store for later processing
            attrs['_new_node_unit'] = new_node_unit
            attrs['_previous_node_unit'] = previous_data['node_unit']

        # Check if dispenser_unit is being changed
        new_dispenser_unit = attrs.get('dispenser_unit')
        if new_dispenser_unit != previous_data['dispenser_unit']:  # This handles both None and actual changes
            if new_dispenser_unit:
                # Check if this dispenser unit is assigned to the same customer
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
            
            # Store for later processing
            attrs['_new_dispenser_unit'] = new_dispenser_unit
            attrs['_previous_dispenser_unit'] = previous_data['dispenser_unit']

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        
        # Get previous data for comparison
        previous_data = {
            'node_unit': instance.node_unit,
            'dispenser_unit': instance.dispenser_unit,
            'fuel_sensor_type': instance.fuel_sensor_type,
            'remarks': instance.remarks,
        }

        # Update fields only if they are provided in the payload
        # If not provided, keep the previous data
        instance.fuel_sensor_type = validated_data.get('fuel_sensor_type', previous_data['fuel_sensor_type'])
        instance.remarks = validated_data.get('remarks', previous_data['remarks'])
        
        # Handle node_unit change
        if '_new_node_unit' in validated_data:
            new_node_unit = validated_data['_new_node_unit']
            previous_node_unit = validated_data['_previous_node_unit']
            
            # Update the instance
            instance.node_unit = new_node_unit
            
            # Mark new node unit as assigned
            new_node_unit.assigned_status = True
            new_node_unit.updated_by = (user.id if user else new_node_unit.updated_by)
            new_node_unit.updated_at = timezone.now()
            new_node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
            
            # Mark previous node unit as unassigned
            previous_node_unit.assigned_status = False
            previous_node_unit.updated_by = (user.id if user else previous_node_unit.updated_by)
            previous_node_unit.updated_at = timezone.now()
            previous_node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])
        else:
            # Keep the same node unit
            instance.node_unit = previous_data['node_unit']

        # Handle dispenser_unit change
        if '_new_dispenser_unit' in validated_data:
            new_dispenser_unit = validated_data['_new_dispenser_unit']
            # Update the instance
            instance.dispenser_unit = new_dispenser_unit
        else:
            # Keep the same dispenser unit
            instance.dispenser_unit = previous_data['dispenser_unit']

        # Update the mapping instance
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
                # Check if both fields are provided
        if 'status' in attrs and 'assigned_status' in attrs:
            raise serializers.ValidationError("Only one field can be updated at a time: either 'status' or 'assigned_status'.")
        
        # Check if no fields are provided
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
                # Update assigned_status field and related unit statuses
        elif 'assigned_status' in validated_data:
            new_assigned_status = validated_data['assigned_status']
            instance.assigned_status = new_assigned_status
            
            # If assigned_status is being disabled, also disable the status field
            if not new_assigned_status:
                instance.status = False

            # Mark node unit as assigned
            instance.node_unit.assigned_status = False
            instance.node_unit.updated_by = user.id
            instance.node_unit.updated_at = timezone.now()
            instance.node_unit.save(update_fields=['assigned_status', 'updated_by', 'updated_at'])  

        instance.save()          
        return instance


class DeleteNodeDispenserCustomerMappingSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate(self, attrs):
        instance = self.context.get('instance')  # Changed from getattr(self, 'instance', None)
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        # Check if assigned_status is True
        if instance.assigned_status is True:
            raise serializers.ValidationError("Cannot delete node dispenser customer mapping that is currently assigned to a customer.")
        return attrs
    
    def delete(self, instance):
        instance.delete()
        return instance 







# class GetDispenserGunMappingListByDeliveryLocationIDsSerializer(serializers.Serializer):
#     delivery_location_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         allow_empty=False
#     )

#     def validate(self, data):
#         delivery_location_ids = data.get("delivery_location_ids", [])
#         user = self.context.get("user")
#         roles = self.context.get("roles", [])

#         if not delivery_location_ids:
#             raise serializers.ValidationError("delivery_location_ids is required.")

#         # ✅ 1. Get direct delivery locations
#         existing_ids = list(
#             DeliveryLocations.objects.filter(id__in=delivery_location_ids)
#             .values_list("id", flat=True)
#         )

#         # ✅ 2. Get delivery_location_ids from DU_Accessible_delivery_locations
#         accessible_ids = list(
#             DeliveryLocation_Mapping_DispenserUnit.objects.filter(
#                 DU_Accessible_delivery_locations__overlap=delivery_location_ids
#             ).values_list("DU_Accessible_delivery_locations", flat=True)
#         )

#         # Flatten the nested lists (JSONField returns arrays)
#         accessible_ids_flat = set()
#         for sublist in accessible_ids:
#             accessible_ids_flat.update(sublist)

#         # ✅ 3. Union both sources
#         found_ids = set(existing_ids) | (set(delivery_location_ids) & accessible_ids_flat)

#         missing_ids = set(delivery_location_ids) - found_ids
#         if missing_ids:
#             raise serializers.ValidationError(
#                 f"Delivery Location IDs not found in main table or DU_Accessible: {', '.join(map(str, missing_ids))}"
#             )

#         # ✅ 4. Role-based restriction
#         if "IOT Admin" in roles:
#             return data

#         # For non-admins, ensure they own these delivery locations
#         for dl_id in found_ids:
#             try:
#                 dl_obj = DeliveryLocations.objects.get(id=dl_id)
#                 if dl_obj.customer_id != user.customer_id:
#                     raise serializers.ValidationError(
#                         f"You do not have access to Delivery Location ID {dl_id}."
#                     )
#             except DeliveryLocations.DoesNotExist:
#                 continue  # If not in direct table, skip access check (already counted above)

#         return data


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

        # ✅ 1. Check that all IDs exist in DeliveryLocations or DU_Accessible
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

        # ✅ 2. If IoT Admin → allow all
        if "IOT Admin" in roles:
            return data

        # ✅ 3. For other roles: check customer ownership
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
        
        # Get user roles from context
        roles = self.context.get("roles", [])

        if DeliveryLocation_Mapping_DispenserUnit.objects.filter(delivery_location_id=delivery_location_id).exists():
            raise serializers.ValidationError("This delivery location id is already exists.")
                
        # Check if dispenser_gun_mapping_id already exists in this table
        if DeliveryLocation_Mapping_DispenserUnit.objects.filter(dispenser_gun_mapping_id=dispenser_gun_mapping_id).exists():
            raise serializers.ValidationError("This dispenser gun mapping is already assigned to a delivery location.")
        
        # Accounts Admin role validation - can only add delivery locations that belong to their customer
        if 'Accounts Admin' in roles:
            # Get the customer ID from the dispenser gun mapping
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                # Check if the delivery location belongs to this customer
                if not DeliveryLocations.objects.filter(id=delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("You can only add delivery locations that belong to your customer.")
                
                # Validate DU_Accessible_delivery_locations - all must belong to the same customer
                if DU_Accessible_delivery_locations:
                    for location_id in DU_Accessible_delivery_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"Delivery location with ID {location_id} does not belong to your customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")
        
        # IOT Admin role validation - ensure all delivery locations belong to the same customer
        elif 'IOT Admin' in roles:
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                # Check if the main delivery location belongs to the same customer as dispenser gun mapping
                if not DeliveryLocations.objects.filter(id=delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("All delivery locations must belong to the same customer as the dispenser gun mapping.")
                
                # Validate DU_Accessible_delivery_locations - all must belong to the same customer
                if DU_Accessible_delivery_locations:
                    for location_id in DU_Accessible_delivery_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"All delivery locations must belong to the same customer. Location ID {location_id} belongs to a different customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")
        
        # Validate DU_Accessible_delivery_locations if provided
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
        """Custom method to get delivery location details"""
        data = super().to_representation(instance)
        
        # Get delivery location details if delivery_location_id exists
        if instance.delivery_location_id:
            try:
                delivery_location = DeliveryLocations.objects.get(id=instance.delivery_location_id)
                # You can add more fields from delivery_location as needed
                data['delivery_location_id'] = {
                    'id': delivery_location.id,
                    'name': delivery_location.name,  # Assuming there's a name field
                    # Add other fields you need
                }
            except DeliveryLocations.DoesNotExist:
                data['delivery_location'] = None
        else:
            data['delivery_location'] = None

            # Get details for DU_Accessible_delivery_locations if they exist
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
                    # Include location even if it doesn't exist (for data integrity)
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
            
            # Check each ID in the list exists in DeliveryLocations
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

        # Read previous data
        previous_data = {
            'delivery_location_id': instance.delivery_location_id,
            'dispenser_gun_mapping_id': instance.dispenser_gun_mapping_id.id if instance.dispenser_gun_mapping_id else None,
            'DU_Accessible_delivery_locations': instance.DU_Accessible_delivery_locations or [],
            'remarks': instance.remarks,
        }

        # Get user roles from context
        roles = self.context.get("roles", [])

        # Check if dispenser_gun_mapping_id is being changed
        new_dispenser_gun_mapping_id = attrs.get('dispenser_gun_mapping_id')
        if new_dispenser_gun_mapping_id is not None:
            # Check if the new dispenser_gun_mapping_id is already assigned to another delivery location mapping
            existing_mapping = DeliveryLocation_Mapping_DispenserUnit.objects.filter(
                dispenser_gun_mapping_id=new_dispenser_gun_mapping_id
            ).exclude(id=instance.id)
            
            if existing_mapping.exists():
                raise serializers.ValidationError("This dispenser gun mapping is already assigned to another delivery location.")

        # Role-based validation for delivery locations
        delivery_location_id = attrs.get('delivery_location_id')
        DU_Accessible_delivery_locations = attrs.get('DU_Accessible_delivery_locations')
        
        # Use new values if provided, otherwise use previous values
        final_delivery_location_id = delivery_location_id if delivery_location_id is not None else previous_data['delivery_location_id']
        final_dispenser_gun_mapping_id = new_dispenser_gun_mapping_id if new_dispenser_gun_mapping_id is not None else previous_data['dispenser_gun_mapping_id']
        final_accessible_locations = DU_Accessible_delivery_locations if DU_Accessible_delivery_locations is not None else previous_data['DU_Accessible_delivery_locations']

        # Accounts Admin role validation - can only edit delivery locations that belong to their customer
        if 'Accounts Admin' in roles:
            # Get the customer ID from the dispenser gun mapping
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=final_dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                # Check if the delivery location belongs to this customer
                if not DeliveryLocations.objects.filter(id=final_delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("You can only edit delivery locations that belong to your customer.")
                
                # Validate DU_Accessible_delivery_locations - all must belong to the same customer
                if final_accessible_locations:
                    for location_id in final_accessible_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"Delivery location with ID {location_id} does not belong to your customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")
        
        # IOT Admin role validation - ensure all delivery locations belong to the same customer
        elif 'IOT Admin' in roles:
            try:
                dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=final_dispenser_gun_mapping_id)
                customer_id = dispenser_gun_mapping.customer
                
                # Check if the main delivery location belongs to the same customer as dispenser gun mapping
                if not DeliveryLocations.objects.filter(id=final_delivery_location_id, customer=customer_id).exists():
                    raise serializers.ValidationError("All delivery locations must belong to the same customer as the dispenser gun mapping.")
                
                # Validate DU_Accessible_delivery_locations - all must belong to the same customer
                if final_accessible_locations:
                    for location_id in final_accessible_locations:
                        if not DeliveryLocations.objects.filter(id=location_id, customer=customer_id).exists():
                            raise serializers.ValidationError(f"All delivery locations must belong to the same customer. Location ID {location_id} belongs to a different customer.")
                            
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                raise serializers.ValidationError("Invalid dispenser gun mapping ID.")

        # Store previous data for use in update method
        attrs['previous_data'] = previous_data
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self.context.get("user", None)
        previous_data = validated_data.pop('previous_data', {})

        # Update fields only if they are provided and different from previous data
        fields_to_update = []
        
        # Check delivery_location_id
        if 'delivery_location_id' in validated_data:
            new_delivery_location_id = validated_data['delivery_location_id']
            if new_delivery_location_id != previous_data['delivery_location_id']:
                instance.delivery_location_id = new_delivery_location_id
                fields_to_update.append('delivery_location_id')

        # Check dispenser_gun_mapping_id
        if 'dispenser_gun_mapping_id' in validated_data:
            new_dispenser_gun_mapping_id = validated_data['dispenser_gun_mapping_id']
            if new_dispenser_gun_mapping_id != previous_data['dispenser_gun_mapping_id']:
                if new_dispenser_gun_mapping_id is not None:
                    dispenser_gun_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=new_dispenser_gun_mapping_id)
                    instance.dispenser_gun_mapping_id = dispenser_gun_mapping
                else:
                    instance.dispenser_gun_mapping_id = None
                fields_to_update.append('dispenser_gun_mapping_id')

        # Check DU_Accessible_delivery_locations
        if 'DU_Accessible_delivery_locations' in validated_data:
            new_accessible_locations = validated_data['DU_Accessible_delivery_locations']
            if new_accessible_locations != previous_data['DU_Accessible_delivery_locations']:
                instance.DU_Accessible_delivery_locations = new_accessible_locations
                fields_to_update.append('DU_Accessible_delivery_locations')

        # Check remarks
        if 'remarks' in validated_data:
            new_remarks = validated_data['remarks']
            if new_remarks != previous_data['remarks']:
                instance.remarks = new_remarks
                fields_to_update.append('remarks')

        # Only update if there are changes
        if fields_to_update:
            instance.updated_by = user.id if user else instance.updated_by
            instance.updated_at = timezone.now()
            fields_to_update.extend(['updated_by', 'updated_at'])
            instance.save(update_fields=fields_to_update)
        else:
            # No changes detected
            pass

        return instance


class DeleteDeliveryLocationMappingDispenserUnitSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
    def validate(self, attrs):
        instance = self.context.get('instance')
        if not instance:
            raise serializers.ValidationError("Instance not found.")
        
        # Get user roles from context
        roles = self.context.get("roles", [])
        
        # Accounts Admin role validation - can only delete delivery location mappings related to their customer
        if 'Accounts Admin' in roles:
            # Get the customer ID from the dispenser gun mapping
            try:
                dispenser_gun_mapping = instance.dispenser_gun_mapping_id
                customer_id = dispenser_gun_mapping.customer
                
                # Check if the delivery location belongs to this customer
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
    delivery_location_id = serializers.IntegerField()
    customer_id = serializers.IntegerField()
    asset_id = serializers.IntegerField()
    request_type = serializers.ChoiceField(choices=[0, 1])  # 0: Volume, 1: Amount
    dispenser_volume = serializers.FloatField(required=False)
    dispenser_price = serializers.FloatField(required=False)
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        user = self.context.get("user")
        login_user_id = getattr(user, "id", None)

        user_id = data.get("user_id")
        delivery_location_id = data.get("delivery_location_id")
        customer_id = data.get("customer_id")
        asset_id = data.get("asset_id")
        request_type = data.get("request_type")
        dispenser_volume = data.get("dispenser_volume")
        dispenser_price = data.get("dispenser_price")

        # 1. Validate user
        try:
            user_obj = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            raise serializers.ValidationError("Invalid user_id")

        if login_user_id != user_id:
            raise serializers.ValidationError("Logged-in user does not match the given user_id")

        data["user_name"] = user_obj.name
        data["user_email"] = user_obj.email
        data["user_phone"] = user_obj.mobile

        # 2. Validate delivery_location
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


        pending_exists = RequestFuelDispensingDetails.objects.filter(
            delivery_location_id=delivery_location_id,
            request_status=0
        ).order_by('-request_created_at').first()

        if pending_exists:
            raise serializers.ValidationError("A fuel dispensing request is already pending for this delivery location. Please wait until it completes.")


        data["delivery_location_name"] = location.name
        if location.customer_id != customer_id:
            raise serializers.ValidationError("Provided customer_id does not match with the delivery location's customer.")
        customer = Customers.objects.get(id=customer_id)
        data["customer_id"] = customer.id
        data["customer_name"] = customer.name
        data["customer_email"] = customer.email
        data["customer_phone"] = customer.mobile

        try:
            dispenser = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_map_id)
        except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
            raise serializers.ValidationError("Dispenser mapping not found")

        try:
            dispenser_unit = DispenserUnits.objects.get(id=dispenser.dispenser_unit.id)
        except DispenserUnits.DoesNotExist:
            raise serializers.ValidationError("Dispenser unit not found")

        data["dispenser_serialnumber"] = dispenser_unit.serial_number
        data["dispenser_imeinumber"] = dispenser_unit.imei_number


        # 3. Validate asset
        try:
            asset = Assets.objects.get(id=asset_id)
        except Assets.DoesNotExist:
            raise serializers.ValidationError("Invalid asset_id")

        if asset.customer_id != data["customer_id"]:
            raise serializers.ValidationError("Asset does not belong to the given customer")
        
        # Check if this asset is accessible to this delivery location
        if not DeliveryLocationAssets.objects.filter(
            delivery_location=delivery_location_id,
            asset_id=asset_id
        ).exists():
            raise serializers.ValidationError("This asset is not accessible to the given delivery location.")


        data["asset_name"] = asset.name
        data["asset_tag_id"] = asset.tag_id
        data["asset_tag_type"] = asset.tag_type
        data["asset_type"] = asset.type

        # 4. Generate unique transaction_id
        while True:
            txn_id = "TXN" + str(random.randint(100000000000, 999999999999))
            if not RequestFuelDispensingDetails.objects.filter(transaction_id=txn_id).exists():
                break
        data["transaction_id"] = txn_id

        # 5. Validate request_type logic
        if request_type == 0:  # Volume
            if dispenser_volume is None:
                raise serializers.ValidationError("dispenser_volume is required when request_type is by Volume")
            data["dispenser_volume"] = dispenser_volume
            data["dispenser_price"] = 0.0
        else:  # Amount
            if dispenser_price is None:
                raise serializers.ValidationError("dispenser_price is required when request_type is by Amount")
            data["dispenser_price"] = dispenser_price
            data["dispenser_volume"] = 0.0

        return data

    def create(self, validated_data):

        remarks = validated_data.get("remarks", "")

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
            asset_tag_id=validated_data["asset_tag_id"],
            asset_tag_type=validated_data["asset_tag_type"],
            asset_type=validated_data["asset_type"],
            transaction_id=validated_data["transaction_id"],
            dispenser_volume=validated_data["dispenser_volume"],
            dispenser_price=validated_data["dispenser_price"],
            dispenser_live_price=0.0,
            request_type=validated_data["request_type"],
            request_status=0,
            fuel_state=False,
            transaction_log={},
            remarks=remarks,
            request_created_at=timezone.now(),
            request_created_by=validated_data["user_id"]
        )

        token_source = f"{validated_data['transaction_id']}:{validated_data['dispenser_serialnumber']}"
        secure_token = salted_hmac("secure_connection", token_source).hexdigest()

        validated_data["secure_token"] = secure_token
        return validated_data

class GetFuelDispensingRequestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestFuelDispensingDetails
        fields = '__all__'
        depth = 1

