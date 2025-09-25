# serializers.py
from rest_framework import serializers
from passlib.hash import bcrypt
from existing_tables.models import *
from .models import *
from django.utils import timezone
from django.db import transaction

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