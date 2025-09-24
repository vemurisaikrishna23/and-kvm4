# serializers.py
from rest_framework import serializers
from passlib.hash import bcrypt
from existing_tables.models import *
from .models import DispenserUnits
from django.utils import timezone

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
    serial_number = serializers.CharField(max_length=100, required=True)
    batch_number = serializers.CharField(max_length=100, required=True)
    imei_number = serializers.CharField(max_length=100, required=True)
    mac_address = serializers.CharField(max_length=100, required=True)
    firmware_version = serializers.CharField(max_length=50, required=True)
    hardware_version = serializers.CharField(max_length=50, required=True)
    production_date = serializers.DateField(required=True)
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