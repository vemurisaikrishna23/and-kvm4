# IoT_Panel/auth.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from existing_tables.models import Users
from rest_framework import exceptions


class ExistingUsersProxy(Users):
    class Meta:
        proxy = True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class ExistingUsersJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token contained no identifiable user", code="token_no_user")
        try:
            return ExistingUsersProxy.objects.get(pk=user_id)
        except ExistingUsersProxy.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found", code="user_not_found")