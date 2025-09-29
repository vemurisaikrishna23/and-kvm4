# views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import *
from existing_tables.models import *
from .renderers import *
import hashlib


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


#For OMS Login API To Django Framework access token
class ValidateTokenAndGetNewAccessToken(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        token = request.data.get('token')
        user_id = request.data.get('user_id')

        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token_id, token_plaintext = token.split("|", 1)
            token_hash = hashlib.sha256(token_plaintext.encode()).hexdigest()
        except ValueError:
            return Response({'error': 'Invalid token format'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            token = PersonalAccessTokens.objects.get(id=token_id, token=token_hash, tokenable_id=user_id)
        except PersonalAccessTokens.DoesNotExist:
            return Response({'error': 'Token verification failed'}, status=status.HTTP_404_NOT_FOUND)

        tokens = get_tokens_for_user(user)
        role = get_user_roles(user_id)

            
        return Response({
            'message': 'Token validated successfully',
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'role': role,
        }, status=status.HTTP_200_OK)


#Get Customers
class GetCustomers(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
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

        if "IOT Admin" in roles:
            dispenser_units = DispenserUnits.objects.all()
            serializer = GetDispenserUnitsSerializer(dispenser_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get dispenser units"}, status=status.HTTP_403_FORBIDDEN)

#Get Unassigned Dispenser Units
class GetUnassignedDispenserUnits(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if "IOT Admin" in roles:
            dispenser_units = DispenserUnits.objects.filter(assigned_status=False)
            serializer = GetDispenserUnitsSerializer(dispenser_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get unassigned dispenser units"}, status=status.HTTP_403_FORBIDDEN)

#Edit Dispenser Unit
class EditDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

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


#Add Gun Unit
class AddGunUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            serializer = CreateGunUnitSerializer(data=request.data, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Gun Unit Created Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#Get Gun Units
class GetGunUnits(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if "IOT Admin" in roles:
            gun_units = GunUnits.objects.all()
            serializer = GetGunUnitsSerializer(gun_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get gun units"}, status=status.HTTP_403_FORBIDDEN)


#Get Unassigned Gun Units
class GetUnassignedGunUnits(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            gun_units = GunUnits.objects.filter(assigned_status=False)
            serializer = GetGunUnitsSerializer(gun_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get unassigned gun units"}, status=status.HTTP_403_FORBIDDEN)

#Edit Gun Unit
class EditGunUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = GunUnits.objects.get(id=id)
            except GunUnits.DoesNotExist:
                return Response({'error': 'Gun Unit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = EditGunUnitSerializer(instance, data=request.data,partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Gun Unit Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a gun unit"}, status=status.HTTP_403_FORBIDDEN)


#Delete Gun Unit
class DeleteGunUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = GunUnits.objects.get(id=id)
            except GunUnits.DoesNotExist:
                return Response({'error': 'Gun Unit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = DeleteGunUnitSerializer(data={'id': id})
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data['instance']
            instance.delete()
            return Response({'message': 'Gun Unit Deleted Successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to delete a gun unit"}, status=status.HTTP_403_FORBIDDEN)



class AddNodeUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            serializer = CreateNodeUnitSerializer(data=request.data, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Node Unit Created Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to add a node unit"}, status=status.HTTP_403_FORBIDDEN)



class GetNodeUnits(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            node_units = NodeUnits.objects.all()
            serializer = GetNodeUnitsSerializer(node_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get node units"}, status=status.HTTP_403_FORBIDDEN)


#Get Unassigned Node Units
class GetUnassignedNodeUnits(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            node_units = NodeUnits.objects.filter(assigned_status=False)
            serializer = GetNodeUnitsSerializer(node_units, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get unassigned node units"}, status=status.HTTP_403_FORBIDDEN)

#Edit Node Unit
class EditNodeUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = NodeUnits.objects.get(id=id)
            except NodeUnits.DoesNotExist:
                return Response({'error': 'Node Unit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = EditNodeUnitSerializer(instance, data=request.data,partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Node Unit Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a node unit"}, status=status.HTTP_403_FORBIDDEN)


#Delete Node Unit
class DeleteNodeUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request,id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = NodeUnits.objects.get(id=id)
            except NodeUnits.DoesNotExist:
                return Response({'error': 'Node Unit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = DeleteNodeUnitSerializer(data={'id': id})
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data['instance']
            instance.delete()
            return Response({'message': 'Node Unit Deleted Successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to delete a node unit"}, status=status.HTTP_403_FORBIDDEN)


class AddDispenserGunMappingToCustomer(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            serializer = CreateDispenserGunMappingToCustomerSerializer(data=request.data, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Dispenser & Gun Unit Mapping to Customer Created Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to add a dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)


#Get Dispenser Gun Mapping to Customer
class GetDispenserGunMappingToCustomer(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            dispenser_gun_mapping_to_customer = Dispenser_Gun_Mapping_To_Customer.objects.all()
            serializer = GetDispenserGunMappingToCustomerSerializer(dispenser_gun_mapping_to_customer, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)


#Get Dispenser Gun Mapping to Customer by Customer ID
class GetDispenserGunMappingToCustomerByCustomerID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if "IOT Admin" in roles:
            dispenser_gun_mapping_to_customer = Dispenser_Gun_Mapping_To_Customer.objects.filter(customer=customer_id)
            serializer = GetDispenserGunMappingToCustomerSerializer(dispenser_gun_mapping_to_customer, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)


#Edit Dispenser Gun Mapping to Customer
class EditDispenserGunMappingToCustomer(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            try:
                instance = Dispenser_Gun_Mapping_To_Customer.objects.get(id=id)
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                return Response({'error': 'Dispenser Gun Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = EditDispenserGunMappingToCustomerSerializer(instance, data=request.data, partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Dispenser Gun Mapping to Customer Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)

class EditStatusAndAssignedStatusOfDispenserGunMappingToCustomer(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            try:
                instance = Dispenser_Gun_Mapping_To_Customer.objects.get(id=id)
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                return Response({'error': 'Dispenser Gun Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = EditStatusAndAssignedStatusOfDispenserGunMappingToCustomerSerializer(instance, data=request.data, partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()                    
                    if 'status' in request.data:
                        return Response({
                            "message": "Status field updated successfully",
                        }, status=status.HTTP_200_OK)
                    elif 'assigned_status' in request.data:
                        return Response({
                            "message": "Assigned status updated successfully",
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            "message": "Dispenser Gun Mapping updated successfully",
                        }, status=status.HTTP_200_OK)
                        
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit the status of a dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)

#Delete Dispenser Gun Mapping to Customer
class DeleteDispenserGunMappingToCustomer(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = Dispenser_Gun_Mapping_To_Customer.objects.get(id=id)
            except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
                return Response({'error': 'Dispenser Gun Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = DeleteDispenserGunMappingToCustomerSerializer(data={'id': id}, context={'instance': instance})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.delete(instance)
                    return Response({'message': 'Dispenser Gun Mapping to Customer Deleted Successfully'}, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to delete a dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)


#Assign Node Unit & Dispenser Gun Mapping to Customer
class AssignNodeUnitAndDispenserGunMappingToCustomer(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            serializer = AssignNodeUnitAndDispenserGunMappingToCustomerSerializer(data=request.data, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Node Unit & Dispenser Gun Mapping to Customer Assigned Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to assign a node unit and dispenser gun mapping to customer"}, status=status.HTTP_403_FORBIDDEN)


#Get Node Dispenser Customer Mapping
class GetNodeDispenserCustomerMapping(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            node_dispenser_customer_mapping = NodeDispenserCustomerMapping.objects.all()
            serializer = GetNodeDispenserCustomerMappingSerializer(node_dispenser_customer_mapping, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get node dispenser customer mapping"}, status=status.HTTP_403_FORBIDDEN)


#Get Node Dispenser Customer Mapping by Customer ID
class GetNodeDispenserCustomerMappingByCustomerID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            node_dispenser_customer_mapping = NodeDispenserCustomerMapping.objects.filter(customer=customer_id)
            serializer = GetNodeDispenserCustomerMappingSerializer(node_dispenser_customer_mapping, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get node dispenser customer mapping"}, status=status.HTTP_403_FORBIDDEN)


#Edit Node Dispenser Customer Mapping
class EditNodeDispenserCustomerMapping(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = NodeDispenserCustomerMapping.objects.get(id=id)
            except NodeDispenserCustomerMapping.DoesNotExist:
                return Response({'error': 'Node Dispenser Customer Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = EditNodeDispenserCustomerMappingSerializer(instance, data=request.data, partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Node Dispenser Customer Mapping Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a node dispenser customer mapping"}, status=status.HTTP_403_FORBIDDEN)


#Edit Status and Assigned Status of Node Dispenser Customer Mapping
class EditStatusAndAssignedStatusOfNodeDispenserCustomerMapping(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if "IOT Admin" in roles:
            try:
                instance = NodeDispenserCustomerMapping.objects.get(id=id)
            except NodeDispenserCustomerMapping.DoesNotExist:
                return Response({'error': 'Node Dispenser Customer Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = EditStatusAndAssignedStatusOfNodeDispenserCustomerMappingSerializer(instance, data=request.data, partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Node Dispenser Customer Mapping Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit the status and assigned status of a node dispenser customer mapping"}, status=status.HTTP_403_FORBIDDEN)


#Delete Node Dispenser Customer Mapping
class DeleteNodeDispenserCustomerMapping(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = NodeDispenserCustomerMapping.objects.get(id=id)
            except NodeDispenserCustomerMapping.DoesNotExist:
                return Response({'error': 'Node Dispenser Customer Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = DeleteNodeDispenserCustomerMappingSerializer(data={'id': id}, context={'instance': instance})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.delete(instance)
                    return Response({'message': 'Node Dispenser Customer Mapping Deleted Successfully'}, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to delete a node dispenser customer mapping"}, status=status.HTTP_403_FORBIDDEN)



# Add Delivery Location Mapping Dispenser Unit
# class AddDeliveryLocationMappingDispenserUnit(APIView):
#     renderer_classes = [IoT_PanelRenderer]
#     permission_classes = [IsAuthenticated]

#     def post(self, request, format=None):
#         user = request.user
#         user_id = getattr(user, "id", None)
#         roles = get_user_roles(user_id)
        
#         if ["IOT Admin", "Customer"] in roles:
#             serializer = AddDeliveryLocationMappingDispenserUnitSerializer(data=request.data, context={"user": user})
#             if serializer.is_valid(raise_exception=True):
#                 try:
#                     serializer.save()
#                     return Response({
#                         "message": "Delivery Location Mapping Dispenser Unit Created Successfully",
#                     }, status=status.HTTP_201_CREATED)
#                 except serializers.ValidationError as e:
#                     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             return Response({"error": "You are not authorized to add a delivery location mapping dispenser unit"}, status=status.HTTP_403_FORBIDDEN)