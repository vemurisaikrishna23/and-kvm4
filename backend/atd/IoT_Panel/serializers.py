# serializers.py
from rest_framework import serializers
from passlib.hash import bcrypt
from existing_tables.models import *

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
