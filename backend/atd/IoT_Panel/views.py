# views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import *
from existing_tables.models import *
from .renderers import *

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_user_roles(user_id):
    return list(
        ModelHasRoles.objects
        .filter(model_type="user", model_id=user_id)
        .select_related("role")
        .values_list("role__name", flat=True)
    )


#Login
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



#GetCustomers
class GetCustomers(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(roles)
        if "IOT Admin" in roles:
            customers = Customers.objects.all()
            serializer = GetCustomersSerializer(customers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get customers"}, status=status.HTTP_403_FORBIDDEN)


# Add Dispenser Unit
class AddDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if "IOT Admin" in roles:
            serializer = CreateDispenserUnitSerializer(data=request.data, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Dispenser Unit Created Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to add a dispenser unit"}, status=status.HTTP_403_FORBIDDEN)

#Get Dispenser Units
class GetDispenserUnits(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(roles)

        if "IOT Admin" in roles:
            dispenser_units = DispenserUnits.objects.all()
            serializer = GetDispenserUnitsSerializer(dispenser_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get dispenser units"}, status=status.HTTP_403_FORBIDDEN)

#Edit Dispenser Unit
class EditDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(roles)

        if "IOT Admin" in roles:
            try:
                instance = DispenserUnits.objects.get(id=id)
            except DispenserUnits.DoesNotExist:
                return Response({'error': 'DispenserUnit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = EditDispenserUnitSerializer(instance, data=request.data,partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Dispenser Unit Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a dispenser unit"}, status=status.HTTP_403_FORBIDDEN)


#Delete Dispenser Unit
class DeleteDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(roles)
        if "IOT Admin" in roles:
            try:
                instance = DispenserUnits.objects.get(id=id)
            except DispenserUnits.DoesNotExist:
                return Response({'error': 'DispenserUnit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = DeleteDispenserUnitSerializer(data={'id': id})
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data['instance']
            instance.delete()
            return Response({'message': 'Dispenser Unit Deleted Successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to delete a dispenser unit"}, status=status.HTTP_403_FORBIDDEN)



