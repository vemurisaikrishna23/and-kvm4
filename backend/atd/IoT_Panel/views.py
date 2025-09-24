# views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import *
from existing_tables.models import *

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    #test

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # check roles
        roles = (
            ModelHasRoles.objects.filter(model_type="user", model_id=user.id)
            .select_related("role")
            .values_list("role__name", flat=True)
        )
        role_names = [r for r in roles if r]

        # enforce IOT Admin only
        if not any(r.lower().replace(" ", "") == "iotadmin" for r in role_names):
            return Response(
                {'error': 'Access denied (IOT Admin only).'},
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'user_id': user.id,
            **tokens
        }, status=status.HTTP_200_OK)


