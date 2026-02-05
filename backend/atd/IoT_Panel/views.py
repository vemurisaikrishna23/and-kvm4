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
from django.db.models import Q, Sum, Count
import time
from datetime import datetime, timedelta

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
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            # For Accounts Admin, validate that they can only access their customer's data
            if "Accounts Admin" in roles:
                try:
                    # Validate using PointOfContacts table
                    # Check if the user belongs to this customer
                    poc = PointOfContacts.objects.filter(
                        user_id=user_id,
                        belong_to_type='customer',
                        belong_to_id=customer_id
                    ).first()
                    
                    if not poc:
                        return Response({
                            "error": "You are not authorized to access this customer's data"
                        }, status=status.HTTP_403_FORBIDDEN)
                    
                    # Get dispenser gun mappings for this specific customer
                    dispenser_gun_mapping_to_customer = Dispenser_Gun_Mapping_To_Customer.objects.filter(
                        customer=customer_id,
                        assigned_status=True
                    )
                except Exception as e:
                    return Response({
                        "error": f"Error retrieving customer data: {str(e)}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            else:
                dispenser_gun_mapping_to_customer = Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer=customer_id,
                    assigned_status=True
                )
            
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
class AddDeliveryLocationMappingDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(roles)
        
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            serializer = AddDeliveryLocationMappingDispenserUnitSerializer(data=request.data, context={"user": user, "roles": roles})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Delivery Location Mapping Dispenser Unit Created Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to add a delivery location mapping dispenser unit"}, status=status.HTTP_403_FORBIDDEN)


#Get Delivery Location Mapping Dispenser Unit
class GetDeliveryLocationMappingDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            delivery_location_mapping_dispenser_unit = DeliveryLocation_Mapping_DispenserUnit.objects.all()
            serializer = GetDeliveryLocationMappingDispenserUnitSerializer(delivery_location_mapping_dispenser_unit, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get delivery location mapping dispenser unit"}, status=status.HTTP_403_FORBIDDEN)


class GetDeliveryLocationMappingDispenserUnitByCustomerID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            # Validate that customer_id matches the customer from dispenser_gun_mapping_id
            delivery_location_mapping_dispenser_unit = DeliveryLocation_Mapping_DispenserUnit.objects.filter(
                dispenser_gun_mapping_id__customer=customer_id
            )
            serializer = GetDeliveryLocationMappingDispenserUnitSerializer(delivery_location_mapping_dispenser_unit, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get delivery location mapping dispenser unit"}, status=status.HTTP_403_FORBIDDEN)


class GetDeliveryLocationMappingDispenserUnitByPOC(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if 'Dispenser' in roles:
            return Response(
                {"error": "You are not authorized to access this data."},
                status=status.HTTP_403_FORBIDDEN
            )

        poc_entries = PointOfContacts.objects.filter(
            user_id=user_id,
            belong_to_type='delivery_location'
        )
        delivery_location_ids = [poc.belong_to_id for poc in poc_entries]

        if not delivery_location_ids:
            return Response(
                {"message": "No delivery locations mapped to this user."},
                status=status.HTTP_200_OK
            )

        direct_matches = DeliveryLocation_Mapping_DispenserUnit.objects.filter(
            delivery_location_id__in=delivery_location_ids
        )

        accessible_matches = []
        for mapping in DeliveryLocation_Mapping_DispenserUnit.objects.all():
            if mapping.DU_Accessible_delivery_locations:
                if any(loc_id in delivery_location_ids for loc_id in mapping.DU_Accessible_delivery_locations):
                    accessible_matches.append(mapping)

        combined_records = list(direct_matches) + accessible_matches

        # Deduplicate based on dispenser_gun_mapping_id
        unique_records = {}
        for record in combined_records:
            gun_map_id = getattr(record.dispenser_gun_mapping_id, "id", None)
            if gun_map_id not in unique_records:
                unique_records[gun_map_id] = record

        final_records = list(unique_records.values())
        serializer = GetDeliveryLocationMappingDispenserUnitSerializer(final_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


#Get Dispenser Gun Mapping List by Delivery Location ID's
class GetDispenserGunMappingListByDeliveryLocationIDs(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        try:
            serializer = GetDispenserGunMappingListByDeliveryLocationIDsSerializer(
                data=request.data,
                context={"roles": roles, "user": user}
            )
            serializer.is_valid(raise_exception=True)
            delivery_location_ids = serializer.validated_data["delivery_location_ids"]

            mappings = DeliveryLocation_Mapping_DispenserUnit.objects.filter(
                Q(delivery_location_id__in=delivery_location_ids) |
                Q(DU_Accessible_delivery_locations__contains=delivery_location_ids) |
                Q(DU_Accessible_delivery_locations__overlap=delivery_location_ids)
            ).distinct()

            result_serializer = GetDeliveryLocationMappingDispenserUnitSerializer(mappings, many=True)
            return Response(result_serializer.data, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


#Edit Delivery Location Mapping Dispenser Unit
class EditDeliveryLocationMappingDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            try:
                instance = DeliveryLocation_Mapping_DispenserUnit.objects.get(id=id)
            except DeliveryLocation_Mapping_DispenserUnit.DoesNotExist:
                return Response({'error': 'Delivery Location Mapping Dispenser Unit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = EditDeliveryLocationMappingDispenserUnitSerializer(instance, data=request.data, partial=True, context={"user": user, "roles": roles})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Delivery Location Mapping Dispenser Unit Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a delivery location mapping dispenser unit"}, status=status.HTTP_403_FORBIDDEN)


class DeleteDeliveryLocationMappingDispenserUnit(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            try:
                instance = DeliveryLocation_Mapping_DispenserUnit.objects.get(id=id)
            except DeliveryLocation_Mapping_DispenserUnit.DoesNotExist:
                return Response({'error': 'Delivery Location Mapping Dispenser Unit with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            serializer = DeleteDeliveryLocationMappingDispenserUnitSerializer(data={'id': id}, context={'instance': instance, 'roles': roles})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.delete(instance)
                    return Response({'message': 'Delivery Location Mapping Dispenser Unit Deleted Successfully'}, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to delete a delivery location mapping dispenser unit"}, status=status.HTTP_403_FORBIDDEN)



class CreateRequestForFuelDispensing(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]
 
    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(user_id)

        try:
            serializer = CreateRequestForFuelDispensingSerializer(
                data=request.data,
                context={"roles": roles, "user": user}
            )
            if serializer.is_valid(raise_exception=True):
                try:
                    response_data = serializer.save()
                    return Response({
                        "message": "Fuel dispensing request created successfully.",
                        "data": {"transaction_id": response_data.get("transaction_id")}
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    print("error", e)
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("error123", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Get Fuel Dispensing Requests
class GetFuelDispensingRequests(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            fuel_dispensing_requests = RequestFuelDispensingDetails.objects.all().order_by('-request_created_at')
            serializer = GetFuelDispensingRequestsSerializer(fuel_dispensing_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get fuel dispensing requests"}, status=status.HTTP_403_FORBIDDEN)


# Get Fuel Dispensing Requests by Customer ID
# class GetFuelDispensingRequestsByCustomerID(APIView):
#     renderer_classes = [IoT_PanelRenderer]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, customer_id, format=None):
#         user = request.user
#         user_id = getattr(user, "id", None)
#         roles = get_user_roles(user_id)

#         if any(role in roles for role in ['IOT Admin', 'Accounts Admin', 'Dispenser Manager', 'Location Manager', 'Dispenser']):

#             if 'Accounts Admin' in roles:
#                 # Accounts Admin can fetch only their associated customer's data
#                 try:
#                     poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
#                     if str(poc.belong_to_id) != str(customer_id):
#                         return Response(
#                             {"error": "You are not authorized to view this customer's fuel dispensing requests."},
#                             status=status.HTTP_403_FORBIDDEN
#                         )
#                 except PointOfContacts.DoesNotExist:
#                     return Response(
#                         {"error": "User is not associated with any customer."},
#                         status=status.HTTP_403_FORBIDDEN
#                     )

#             # Base queryset for this customer
#             qs = RequestFuelDispensingDetails.objects.filter(customer_id=customer_id)

#             start_date_str = request.query_params.get('start_date')
#             end_date_str = request.query_params.get('end_date')


#             if start_date_str:
#                 try:
#                     start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
#                     start_dt = datetime.combine(start_date, datetime.min.time())
#                     qs = qs.filter(request_created_at__gte=start_dt)
#                 except ValueError:
#                     return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."},
#                                     status=status.HTTP_400_BAD_REQUEST)

#             if end_date_str:
#                 try:
#                     end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
#                     end_dt = datetime.combine(end_date, datetime.max.time())
#                     qs = qs.filter(request_created_at__lte=end_dt)
#                 except ValueError:
#                     return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."},
#                                     status=status.HTTP_400_BAD_REQUEST)

#             fuel_dispensing_requests = qs.order_by('-request_created_at')
#             serializer = GetFuelDispensingRequestsSerializer(fuel_dispensing_requests, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)

#         else:
#             return Response(
#                 {"error": "You are not authorized to get fuel dispensing requests."},
#                 status=status.HTTP_403_FORBIDDEN
#             )


class GetFuelDispensingRequestsByCustomerID(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # --------------------------------------------------------------------------------
        # ROLE VALIDATION
        # --------------------------------------------------------------------------------
        allowed_roles = [
            'IOT Admin', 'Accounts Admin', 'Dispenser Manager',
            'Location Manager', 'Dispenser'
        ]

        if not any(role in roles for role in allowed_roles):
            return Response(
                {"error": "You are not authorized to get fuel dispensing requests."},
                status=status.HTTP_403_FORBIDDEN
            )

        # --------------------------------------------------------------------------------
        # ACCOUNTS ADMIN CAN ONLY ACCESS THEIR CUSTOMER
        # --------------------------------------------------------------------------------
        if 'Accounts Admin' in roles:
            try:
                poc = PointOfContacts.objects.get(
                    user_id=user_id, belong_to_type="customer"
                )
                if str(poc.belong_to_id) != str(customer_id):
                    return Response(
                        {"error": "You are not authorized to view this customer's fuel dispensing requests."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except PointOfContacts.DoesNotExist:
                return Response(
                    {"error": "User is not associated with any customer."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # --------------------------------------------------------------------------------
        # BASE QUERYSET
        # --------------------------------------------------------------------------------
        qs = RequestFuelDispensingDetails.objects.filter(customer_id=customer_id)

        # --------------------------------------------------------------------------------
        # DISPENSER MANAGER LOGIC
        # --------------------------------------------------------------------------------
        if 'Dispenser Manager' in roles:

            # 1. Fetch customers assigned to this manager
            manager_customers = list(
                PointOfContacts.objects.filter(
                    user_id=user_id,
                    belong_to_type="customer"
                ).values_list("belong_to_id", flat=True)
            )

            # 2. Get dispenser-gun mappings for these customers
            assigned_dispensers = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer__in=manager_customers
                ).values_list("dispenser_unit_id", flat=True)
            )

            # 3. Filter transactions belonging to those dispensers
            qs = qs.filter(dispenser_gun_mapping_id__in=assigned_dispensers)

        # --------------------------------------------------------------------------------
        # LOCATION MANAGER LOGIC
        # --------------------------------------------------------------------------------
        # -------------------------------------------------------------------------
# LOCATION MANAGER LOGIC (IMPROVED + FULLY CORRECT)
# -------------------------------------------------------------------------
        if 'Location Manager' in roles:

            # 1. Manager assigned locations from POC table
            assigned_locations_raw = list(
                PointOfContacts.objects.filter(
                    user_id=user_id,
                    belong_to_type="delivery_location"
                ).values_list("belong_to_id", flat=True)
            )

            # Normalize to integers
            assigned_locations = [int(x) for x in assigned_locations_raw if str(x).isdigit()]

            # Build the filter
            location_filter = Q()

            # Condition 1: direct delivery location match
            location_filter |= Q(delivery_location_id__in=assigned_locations)

            # Condition 2: DU Accessible Locations (JSON list)
            for loc in assigned_locations:
                location_filter |= Q(DU_Accessible_delivery_locations__contains=[loc])

            qs = qs.filter(location_filter).distinct()


        # --------------------------------------------------------------------------------
        # DATE FILTERS
        # --------------------------------------------------------------------------------
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                qs = qs.filter(request_created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                end_dt = datetime.combine(end_date, datetime.max.time())
                qs = qs.filter(request_created_at__lte=end_dt)
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # --------------------------------------------------------------------------------
        # FINAL RESPONSE
        # --------------------------------------------------------------------------------
        qs = qs.order_by('-request_created_at')
        serializer = GetFuelDispensingRequestsSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#Get Fuel Dispensing Requests by Dispenser Gun Mapping ID
class GetFuelDispensingRequestsByDispenserGunMappingID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, dispenser_gun_mapping_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        try:
            dispenser_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(id=dispenser_gun_mapping_id)
        except Dispenser_Gun_Mapping_To_Customer.DoesNotExist:
            return Response({"error": "Dispenser Gun Mapping ID not found."}, status=status.HTTP_404_NOT_FOUND)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin','Dispenser Manager','Location Manager','Dispenser']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                if dispenser_mapping.customer != poc.belong_to_id:
                    return Response({"error": "You are not authorized to access this dispenser's data."}, status=status.HTTP_403_FORBIDDEN)

            requests = RequestFuelDispensingDetails.objects.filter(dispenser_gun_mapping_id=dispenser_gun_mapping_id).order_by('-request_created_at')
            serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)



# Get Fuel Dispensing Requests by Delivery Location ID or Accessible Locations
class GetFuelDispensingRequestsByDeliveryLocationID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, delivery_location_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # 1️⃣ Validate that delivery location exists
        try:
            delivery_location = DeliveryLocations.objects.get(id=delivery_location_id)
        except DeliveryLocations.DoesNotExist:
            return Response(
                {"error": "Delivery Location ID not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2️⃣ Access allowed roles
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin', 'Dispenser Manager', 'Location Manager', 'Dispenser']):
            
            # 3️⃣ For Accounts Admin → validate customer association
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response(
                        {"error": "You are not associated with any customer."},
                        status=status.HTTP_403_FORBIDDEN
                    )

                if delivery_location.customer_id != poc.belong_to_id:
                    return Response(
                        {"error": "You are not authorized to access this dispenser's data."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # 4️⃣ Query 1: direct matches
            direct_matches = RequestFuelDispensingDetails.objects.filter(
                delivery_location_id=delivery_location_id
            )

            # 5️⃣ Query 2: accessible matches — loop since MySQL doesn't support overlap
            accessible_matches = []
            for req in RequestFuelDispensingDetails.objects.exclude(DU_Accessible_delivery_locations=None):
                du_list = req.DU_Accessible_delivery_locations or []
                if isinstance(du_list, list) and delivery_location_id in du_list:
                    accessible_matches.append(req)

            # 6️⃣ Combine both
            all_matches = list(direct_matches) + accessible_matches

            # 7️⃣ Deduplicate (in case same record matched both)
            unique_records = {req.id: req for req in all_matches}
            final_requests = list(unique_records.values())

            # 8️⃣ Serialize
            serializer = GetFuelDispensingRequestsSerializer(final_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(
                {"error": "You are not authorized to access this data."},
                status=status.HTTP_403_FORBIDDEN
            )


# #Get Fuel Dispensing Requests by Delivery Location ID
# class GetFuelDispensingRequestsByDeliveryLocationID(APIView):
#     renderer_classes = [IoT_PanelRenderer]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, delivery_location_id, format=None):
#         user = request.user
#         user_id = getattr(user, "id", None)
#         roles = get_user_roles(user_id)
#         try:
#             delivery_location = DeliveryLocations.objects.get(id=delivery_location_id)
#         except DeliveryLocations.DoesNotExist:
#             return Response({"error": "Delivery Location ID not found."}, status=status.HTTP_404_NOT_FOUND)
#         if any(role in roles for role in ['IOT Admin', 'Accounts Admin','Dispenser Manager','Location Manager','Dispenser']):
#             if 'Accounts Admin' in roles:
#                 try:
#                     poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
#                 except PointOfContacts.DoesNotExist:
#                     return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

#                 if delivery_location.customer_id != poc.belong_to_id:
#                     return Response({"error": "You are not authorized to access this dispenser's data."}, status=status.HTTP_403_FORBIDDEN)
#             requests = RequestFuelDispensingDetails.objects.filter(delivery_location_id=delivery_location_id).order_by('-request_created_at')
#             serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)



class ConsumptionPageDashBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # ----------------------------------------------------------------------
        # BASE QUERYSET
        # ----------------------------------------------------------------------
        qs = RequestFuelDispensingDetails.objects.filter(
            customer_id=customer_id,
            dispenser_received_volume__isnull=False
        )

        # ----------------------------------------------------------------------
        # DATE FILTERS
        # ----------------------------------------------------------------------
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                qs = qs.filter(request_created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "Invalid start_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                end_dt = datetime.combine(end_date, datetime.max.time())
                qs = qs.filter(request_created_at__lte=end_dt)
            except ValueError:
                return Response(
                    {"error": "Invalid end_date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # ----------------------------------------------------------------------
        # ROLE FILTERING — SAME LOGIC FOR BOTH SECTIONS
        # ----------------------------------------------------------------------

        # ACCOUNTS ADMIN
        if "Accounts Admin" in roles:
            try:
                poc = PointOfContacts.objects.get(
                    user_id=user_id,
                    belong_to_type="customer"
                )
                if str(poc.belong_to_id) != str(customer_id):
                    return Response(
                        {"error": "Not authorized for this customer"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except PointOfContacts.DoesNotExist:
                return Response(
                    {"error": "User is not linked to any customer"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # DISPENSER MANAGER
        if "Dispenser Manager" in roles:

            assigned_customers = list(
                PointOfContacts.objects.filter(
                    user_id=user_id,
                    belong_to_type="customer"
                ).values_list("belong_to_id", flat=True)
            )

            assigned_dispensers = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer__in=assigned_customers
                ).values_list("id", flat=True)
            )

            qs = qs.filter(dispenser_gun_mapping_id__in=assigned_dispensers)

        # LOCATION MANAGER
        if "Location Manager" in roles:

            assigned_locations_raw = list(
                PointOfContacts.objects.filter(
                    user_id=user_id,
                    belong_to_type="delivery_location"
                ).values_list("belong_to_id", flat=True)
            )

            assigned_locations = [int(x) for x in assigned_locations_raw if str(x).isdigit()]

            location_filter = Q(delivery_location_id__in=assigned_locations)

            for loc in assigned_locations:
                location_filter |= Q(DU_Accessible_delivery_locations__contains=[loc])

            qs = qs.filter(location_filter).distinct()

        # ----------------------------------------------------------------------
        # 1️⃣ CONSUMING ASSETS
        # ----------------------------------------------------------------------
        asset_rows = (
            qs.values("asset_id", "asset_name")
            .annotate(
                total_volume=Sum("dispenser_received_volume"),
                txn_count=Count("id")
            )
            .order_by("-total_volume")[:10]
        )

        consuming_assets = []
        rank = 1
        for row in asset_rows:
            volume = row["total_volume"] or 0
            tx = row["txn_count"] or 0
            avg = volume / tx if tx > 0 else 0

            consuming_assets.append({
                "rank": rank,
                "asset_id": row["asset_id"],
                "asset_name": row["asset_name"],
                "consumption_liters": round(volume, 2),
                "transactions": tx,
                "avg_per_transaction": round(avg, 2)
            })
            rank += 1

        # ----------------------------------------------------------------------
        # 2️⃣ CONSUMING USERS
        # ----------------------------------------------------------------------
        user_rows = (
            qs.values("user_id", "user_name")
            .annotate(
                total_volume=Sum("dispenser_received_volume"),
                txn_count=Count("id")
            )
            .order_by("-total_volume")[:10]
        )

        consuming_users = []
        rank = 1
        for row in user_rows:
            volume = row["total_volume"] or 0
            tx = row["txn_count"] or 0
            avg = volume / tx if tx > 0 else 0

            consuming_users.append({
                "rank": rank,
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "consumption_liters": round(volume, 2),
                "transactions": tx,
                "avg_per_transaction": round(avg, 2)
            })
            rank += 1

        # ----------------------------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------------------------
        return Response({
            "consuming_assets": consuming_assets,
            "consuming_users": consuming_users
        }, status=status.HTTP_200_OK)



class DailyReconciliationDashBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # ----------------------------------------------------------
        # DATE RANGE
        # ----------------------------------------------------------
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "start_date and end_date required"},
                status=400
            )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except:
            return Response({"error": "Invalid date"}, status=400)

        # ----------------------------------------------------------
        # BASE QUERYSET
        # ----------------------------------------------------------
        qs = RequestFuelDispensingDetails.objects.filter(
            customer_id=customer_id,
            request_created_at__date__gte=start_date,
            request_created_at__date__lte=end_date
        )

        # ----------------------------------------------------------
        # ROLE FILTERING
        # ----------------------------------------------------------

        # ACCOUNTS ADMIN
        if "Accounts Admin" in roles:
            try:
                poc = PointOfContacts.objects.get(
                    user_id=user_id,
                    belong_to_type="customer"
                )
                if str(poc.belong_to_id) != str(customer_id):
                    return Response({"error": "Not authorized"}, status=403)
            except PointOfContacts.DoesNotExist:
                return Response({"error": "Not authorized"}, status=403)

        # DISPENSER MANAGER
        if "Dispenser Manager" in roles:
            assigned_customers = list(
                PointOfContacts.objects.filter(
                    user_id=user_id,
                    belong_to_type="customer"
                ).values_list("belong_to_id", flat=True)
            )

            assigned_dispensers = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer__in=assigned_customers
                ).values_list("id", flat=True)
            )

            qs = qs.filter(dispenser_gun_mapping_id__in=assigned_dispensers)

        # LOCATION MANAGER
        if "Location Manager" in roles:
            assigned_locations_raw = list(
                PointOfContacts.objects.filter(
                    user_id=user_id,
                    belong_to_type="delivery_location"
                ).values_list("belong_to_id", flat=True)
            )

            assigned_locations = [int(x) for x in assigned_locations_raw if str(x).isdigit()]

            location_filter = Q(delivery_location_id__in=assigned_locations)

            for loc in assigned_locations:
                location_filter |= Q(DU_Accessible_delivery_locations__contains=[loc])

            qs = qs.filter(location_filter).distinct()

        # ----------------------------------------------------------
        # RECONCILIATION PROCESS
        # ----------------------------------------------------------
        results = []

        # Group by dispenser
        dispensers = qs.values(
            "dispenser_gun_mapping_id",
            "dispenser_serialnumber",
        ).distinct()

        for disp in dispensers:
            disp_id = disp["dispenser_gun_mapping_id"]
            serial = disp["dispenser_serialnumber"]

            current_date = start_date
            while current_date <= end_date:

                daily_qs = qs.filter(
                    dispenser_gun_mapping_id=disp_id,
                    request_created_at__date=current_date
                ).order_by("request_created_at")

                if daily_qs.exists():

                    # Opening
                    first_rec = daily_qs.first()
                    opening = first_rec.totalizer_volume_starting or 0

                    # Closing
                    last_rec = daily_qs.last()
                    closing = last_rec.totalizer_volume_ending

                    if closing is None:
                        last_non_null = daily_qs.filter(
                            totalizer_volume_ending__isnull=False
                        ).order_by("-request_created_at").first()

                        if last_non_null:
                            closing = last_non_null.totalizer_volume_ending
                        else:
                            closing = opening

                    # Total dispensed
                    total_dispensed = round(closing - opening, 2)

                    # Approved volume
                    approved = (
                        daily_qs.aggregate(total=Sum("dispenser_received_volume")).get("total") or 0
                    )

                    variance = round(total_dispensed - approved, 2)

                    status_label = "Reconciled" if variance == 0 else "Variance"

                    results.append({
                        "date": str(current_date),
                        "dispenser_id": disp_id,
                        "dispenser_serialnumber": serial,
                        "opening_reading": round(opening, 2),
                        "closing_reading": round(closing, 2),
                        "total_dispensed": round(total_dispensed, 2),
                        "approved_volume": round(approved, 2),
                        "variance": variance,
                        "status": status_label
                    })

                current_date += timedelta(days=1)

        return Response(results, status=200)



# class OverviewDashboard(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, customer_id, format=None):
#         user = request.user
#         user_id = getattr(user, "id", None)
#         roles = get_user_roles(user_id)

#         # ----------------------------------------------------------
#         # DATE FILTERS (optional but recommended for daywise logs)
#         # ----------------------------------------------------------
#         start_date_str = request.query_params.get("start_date")
#         end_date_str = request.query_params.get("end_date")

#         if start_date_str and end_date_str:
#             try:
#                 start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#                 end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#             except ValueError:
#                 return Response(
#                     {"error": "Invalid date format. Use YYYY-MM-DD"},
#                     status=400
#                 )
#         else:
#             # Default: Last 15 days
#             end_date = datetime.now().date()
#             start_date = end_date - timedelta(days=14)

#         # ----------------------------------------------------------
#         # BASE QUERYSET
#         # ----------------------------------------------------------
#         qs = RequestFuelDispensingDetails.objects.filter(
#             customer_id=customer_id,
#             request_created_at__date__gte=start_date,
#             request_created_at__date__lte=end_date
#         )

#         # ----------------------------------------------------------
#         # ROLE FILTERING
#         # ----------------------------------------------------------

#         # ACCOUNTS ADMIN
#         if "Accounts Admin" in roles:
#             try:
#                 poc = PointOfContacts.objects.get(
#                     user_id=user_id, belong_to_type="customer"
#                 )
#                 if str(poc.belong_to_id) != str(customer_id):
#                     return Response({"error": "Not authorized"}, status=403)
#             except PointOfContacts.DoesNotExist:
#                 return Response({"error": "Not authorized"}, status=403)

#         # DISPENSER MANAGER
#         if "Dispenser Manager" in roles:

#             assigned_customers = list(
#                 PointOfContacts.objects.filter(
#                     user_id=user_id, belong_to_type="customer"
#                 ).values_list("belong_to_id", flat=True)
#             )

#             assigned_dispensers = list(
#                 Dispenser_Gun_Mapping_To_Customer.objects.filter(
#                     customer__in=assigned_customers
#                 ).values_list("id", flat=True)
#             )

#             qs = qs.filter(dispenser_gun_mapping_id__in=assigned_dispensers)

#         # LOCATION MANAGER
#         if "Location Manager" in roles:

#             assigned_locations_raw = list(
#                 PointOfContacts.objects.filter(
#                     user_id=user_id, belong_to_type="delivery_location"
#                 ).values_list("belong_to_id", flat=True)
#             )

#             assigned_locations = [int(x) for x in assigned_locations_raw if str(x).isdigit()]

#             location_filter = Q(delivery_location_id__in=assigned_locations)
#             for loc in assigned_locations:
#                 location_filter |= Q(DU_Accessible_delivery_locations__contains=[loc])

#             qs = qs.filter(location_filter).distinct()

#         # ----------------------------------------------------------
#         # AGGREGATED OVERVIEW (TOP BLOCK)
#         # ----------------------------------------------------------

#         total_transactions = qs.count()

#         agg = qs.aggregate(
#             total_volume=Sum("dispenser_received_volume"),
#             total_price=Sum("dispenser_received_price")
#         )

#         total_volume_dispensed = agg["total_volume"] or 0
#         total_price_dispensed = agg["total_price"] or 0

#         total_assets = qs.values("asset_id").distinct().count()

#         # ----------------------------------------------------------
#         # FUEL AMOUNT CONSUMPTION (DAYWISE LOG)
#         # ----------------------------------------------------------

#         fuel_amount_consumption = []
#         current_date = start_date

#         grand_total_volume = 0
#         grand_total_price = 0

#         while current_date <= end_date:

#             day_qs = qs.filter(request_created_at__date=current_date)

#             if day_qs.exists():
#                 day_volume = (
#                     day_qs.aggregate(v=Sum("dispenser_received_volume")).get("v") or 0
#                 )
#                 day_price = (
#                     day_qs.aggregate(p=Sum("dispenser_received_price")).get("p") or 0
#                 )

#                 grand_total_volume += day_volume
#                 grand_total_price += day_price

#                 fuel_amount_consumption.append({
#                     "date": str(current_date),
#                     "total_volume_dispensed": round(day_volume, 2),
#                     "total_price_dispensed": round(day_price, 2)
#                 })

#             current_date += timedelta(days=1)

#         # ----------------------------------------------------------
#         # FINAL PAYLOAD
#         # ----------------------------------------------------------
#         return Response({
#             "total_transactions": total_transactions,
#             "total_volume_dispensed": round(total_volume_dispensed, 2),
#             "total_price_dispensed": round(total_price_dispensed, 2),
#             "total_assets": total_assets,

#             "fuel_amount_consumption": {
#                 "daywise": fuel_amount_consumption,
#                 "grand_total_volume": round(grand_total_volume, 2),
#                 "grand_total_price": round(grand_total_price, 2)
#             }

#         }, status=200)


from django.db.models import Q, Sum, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta


class OverviewDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # ----------------------------------------------------------------------
        # DATE RANGE HANDLING
        # ----------------------------------------------------------------------
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)
        else:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=14)

        # ----------------------------------------------------------------------
        # BASE QUERYSET
        # ----------------------------------------------------------------------
        qs = RequestFuelDispensingDetails.objects.filter(
            customer_id=customer_id,
            request_created_at__date__gte=start_date,
            request_created_at__date__lte=end_date
        )

        # ----------------------------------------------------------------------
        # ROLE LOGIC
        # ----------------------------------------------------------------------

        # ACCOUNTS ADMIN
        if "Accounts Admin" in roles:
            try:
                poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                if str(poc.belong_to_id) != str(customer_id):
                    return Response({"error": "Not authorized for this customer"}, status=403)
            except PointOfContacts.DoesNotExist:
                return Response({"error": "Not authorized"}, status=403)

        # DISPENSER MANAGER
        assigned_customers = []
        assigned_dispensers = []
        if "Dispenser Manager" in roles:
            assigned_customers = list(
                PointOfContacts.objects.filter(user_id=user_id, belong_to_type="customer")
                .values_list("belong_to_id", flat=True)
            )

            assigned_dispensers = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer__in=assigned_customers
                ).values_list("id", flat=True)
            )

            qs = qs.filter(dispenser_gun_mapping_id__in=assigned_dispensers)

        # LOCATION MANAGER
        assigned_locations = []
        if "Location Manager" in roles:
            assigned_locations_raw = list(
                PointOfContacts.objects.filter(
                    user_id=user_id, belong_to_type="delivery_location"
                ).values_list("belong_to_id", flat=True)
            )

            assigned_locations = [int(x) for x in assigned_locations_raw if str(x).isdigit()]

            location_filter = Q(delivery_location_id__in=assigned_locations)

            for loc in assigned_locations:
                location_filter |= Q(DU_Accessible_delivery_locations__contains=[loc])

            qs = qs.filter(location_filter).distinct()

        # ----------------------------------------------------------------------
        # 1) OVERVIEW STATS
        # ----------------------------------------------------------------------
        total_transactions = qs.count()

        agg = qs.aggregate(
            total_volume=Sum("dispenser_received_volume"),
            total_price=Sum("dispenser_received_price")
        )

        total_volume_dispensed = round(agg["total_volume"] or 0, 2)
        total_price_dispensed = round(agg["total_price"] or 0, 2)
        total_assets = qs.values("asset_id").distinct().count()

        # ----------------------------------------------------------------------
        # 2) FUEL & AMOUNT CONSUMPTION (DAYWISE)
        # ----------------------------------------------------------------------
        fuel_amount_daywise = []
        grand_total_volume = 0
        grand_total_price = 0

        current_date = start_date
        while current_date <= end_date:
            day_qs = qs.filter(request_created_at__date=current_date)

            if day_qs.exists():
                day_volume = day_qs.aggregate(v=Sum("dispenser_received_volume")).get("v") or 0
                day_price = day_qs.aggregate(p=Sum("dispenser_received_price")).get("p") or 0

                grand_total_volume += day_volume
                grand_total_price += day_price

                fuel_amount_daywise.append({
                    "date": str(current_date),
                    "total_volume_dispensed": round(day_volume, 2),
                    "total_price_dispensed": round(day_price, 2),
                })

            current_date += timedelta(days=1)

        # ----------------------------------------------------------------------
        # 3) ASSET vs VIN REQUEST COUNT (DAYWISE)
        # ----------------------------------------------------------------------
        asset_vin_daywise = []
        grand_asset_request_count = 0
        grand_vin_request_count = 0

        current_date = start_date
        while current_date <= end_date:
            day_qs = qs.filter(request_created_at__date=current_date)

            if day_qs.exists():
                asset_requests = day_qs.filter(request_vehicle=0).count()
                vin_requests = day_qs.filter(request_vehicle=1).count()

                total_day_requests = asset_requests + vin_requests

                grand_asset_request_count += asset_requests
                grand_vin_request_count += vin_requests

                asset_vin_daywise.append({
                    "date": str(current_date),
                    "asset_request_count": asset_requests,
                    "vin_request_count": vin_requests,
                    "total_request_count": total_day_requests
                })

            current_date += timedelta(days=1)

        grand_total_requests = grand_asset_request_count + grand_vin_request_count

        # ----------------------------------------------------------------------
        # 4) DISPENSER UNIT WISE CONSUMPTION (ALL DISPENSERS)
        # ----------------------------------------------------------------------

        # Fetch dispensers based on role
        if "Accounts Admin" in roles:
            dispenser_list = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer=customer_id
                ).values("id", "dispenser_unit__serial_number")
            )

        elif "Dispenser Manager" in roles:
            dispenser_list = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    customer__in=assigned_customers
                ).values("id", "dispenser_unit__serial_number")
            )

        elif "Location Manager" in roles:
            dispenser_list = list(
                Dispenser_Gun_Mapping_To_Customer.objects.filter(
                    Q(deliverylocation_mapping_dispenserunit__delivery_location_id__in=assigned_locations)
                    |
                    Q(deliverylocation_mapping_dispenserunit__DU_Accessible_delivery_locations__overlap=assigned_locations)
                )
                .values("id", "dispenser_unit__serial_number")
                .distinct()
            )
        else:
            dispenser_list = []

        dispenser_unit_wise = []
        grand_dispenser_total_volume = 0
        grand_dispenser_total_price = 0
        grand_dispenser_total_transactions = 0

        for disp in dispenser_list:
            disp_id = disp["id"]
            serial = disp["dispenser_unit__serial_number"]

            disp_qs = qs.filter(dispenser_gun_mapping_id=disp_id)

            volume = disp_qs.aggregate(v=Sum("dispenser_received_volume")).get("v") or 0
            price = disp_qs.aggregate(p=Sum("dispenser_received_price")).get("p") or 0
            tx = disp_qs.count()

            grand_dispenser_total_volume += volume
            grand_dispenser_total_price += price
            grand_dispenser_total_transactions += tx

            dispenser_unit_wise.append({
                "dispenser_id": disp_id,
                "dispenser_serialnumber": serial,
                "total_volume_dispensed": round(volume, 2),
                "total_price_dispensed": round(price, 2),
                "transactions_count": tx
            })

        # ----------------------------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------------------------
        return Response({
            "total_transactions": total_transactions,
            "total_volume_dispensed": total_volume_dispensed,
            "total_price_dispensed": total_price_dispensed,
            "total_assets": total_assets,

            "fuel_amount_consumption": {
                "daywise": fuel_amount_daywise,
                "grand_total_volume": round(grand_total_volume, 2),
                "grand_total_price": round(grand_total_price, 2)
            },

            "asset_vin_count": {
                "daywise": asset_vin_daywise,
                "grand_asset_request_count": grand_asset_request_count,
                "grand_vin_request_count": grand_vin_request_count,
                "grand_total_requests": grand_total_requests
            },

            "dispenser_unit_wise_consumption": {
                "units": dispenser_unit_wise,
                "grand_total_volume": round(grand_dispenser_total_volume, 2),
                "grand_total_price": round(grand_dispenser_total_price, 2),
                "grand_total_transactions": grand_dispenser_total_transactions
            }

        }, status=200)


#Get Fuel Dispensing Requests by Asset ID
class GetFuelDispensingRequestsByAssetID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        try:
            asset = Assets.objects.get(id=asset_id)
        except Assets.DoesNotExist:
            return Response({"error": "Asset ID not found."}, status=status.HTTP_404_NOT_FOUND)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin','Dispenser Manager','Location Manager','Dispenser']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                if asset.customer_id != poc.belong_to_id:
                    return Response({"error": "You are not authorized to access this asset's data."}, status=status.HTTP_403_FORBIDDEN)

            requests = RequestFuelDispensingDetails.objects.filter(asset_id=asset_id).order_by('-request_created_at')
            serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)



class GetFuelDispensingRequestsByID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print("roles", roles)

        try:
            request_obj = RequestFuelDispensingDetails.objects.get(id=id)
        except RequestFuelDispensingDetails.DoesNotExist:
            return Response({"error": "Fuel Dispensing Request ID not found."}, status=status.HTTP_404_NOT_FOUND)

        if any(role in roles for role in ['IOT Admin', 'Accounts Admin','Dispenser Manager','Location Manager','Dispenser']):

            if 'Accounts Admin' in roles:
                # Check if the logged-in user is mapped to the same customer
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                if request_obj.customer_id != poc.belong_to_id:
                    return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)

            serializer = GetFuelDispensingRequestsSerializerWithTransactionLog(request_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)    
        return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)


#Get Fuel Dispensing Requests by User ID
class GetFuelDispensingRequestsByUserID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, format=None):
        user = request.user
        login_user_id = getattr(user, "id", None)
        roles = get_user_roles(login_user_id)

        try:
            target_user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # If Accounts Admin – check if target_user belongs to their customer
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin','Dispenser Manager','Location Manager','Dispenser']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=login_user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                target_poc = PointOfContacts.objects.filter(user_id=user_id, belong_to_type="customer", belong_to_id=poc.belong_to_id).first()
                if not target_poc:
                    return Response({"error": "This user does not belong to your customer."}, status=status.HTTP_403_FORBIDDEN)
            # Valid: same customer
            requests = RequestFuelDispensingDetails.objects.filter(user_id=user_id).order_by('-request_created_at')
            serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # For all other roles – deny
        return Response({"error": "You are not authorized to view fuel dispensing requests."}, status=status.HTTP_403_FORBIDDEN)


#Add VIN Vehicle
class AddVINVehicle(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        roles = get_user_roles(user.id)

        # Only these roles can add VINs
        if not any(role in roles for role in ['IOT Admin', 'Accounts Admin', 'Dispenser Manager', 'Location Manager']):
            return Response(
                {"error": "You are not authorized to add VIN vehicles."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddVINVehicleSerializer(data=request.data, context={"user": user, "roles": roles})
        serializer.is_valid(raise_exception=True)
        vin_vehicle = serializer.save()

        return Response(
            {
                "message": "VIN Vehicle Created Successfully",
                "transaction_id": vin_vehicle.transaction_id,
                "vin_id": vin_vehicle.id
            },
            status=status.HTTP_201_CREATED
        )


class GetVINVehicleByVIN(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, vin, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # 1) VIN exists?
        vin_vehicle = VIN_Vehicle.objects.filter(vin=vin).order_by('-id').first()
        if not vin_vehicle:
            return Response({"error": "VIN not found."}, status=status.HTTP_404_NOT_FOUND)

        # Already used?
        if vin_vehicle.status is True:
            return Response(
                {"error": "VIN already used for fuel dispensing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2) If POC list is empty -> allow anyone (authenticated) to view
        poc_ids = vin_vehicle.point_of_contact_id or []
        if not poc_ids:
            serializer = GetVINVehicleSerializer(vin_vehicle)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 3) Role-based access (only enforced when poc_ids is non-empty)
        if 'IOT Admin' in roles:
            pass  # full access
        elif any(role in roles for role in ['Accounts Admin', 'Dispenser Manager', 'Location Manager', 'Dispenser']):
            if user_id not in poc_ids:
                return Response(
                    {"error": "You are not authorized to access this VIN."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"error": "You are not authorized to access this VIN."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 4) OK -> return data
        serializer = GetVINVehicleSerializer(vin_vehicle)
        return Response(serializer.data, status=status.HTTP_200_OK)




class GetVINVehicleByID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, vin_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # ---------- 1️⃣ Fetch VIN ----------
        try:
            vin_vehicle = VIN_Vehicle.objects.get(id=vin_id)
        except VIN_Vehicle.DoesNotExist:
            return Response({"error": "VIN vehicle not found."}, status=status.HTTP_404_NOT_FOUND)

        # ---------- 2️⃣ Role-based Authorization ----------
        if "IOT Admin" in roles:
            pass  # full access

        elif "Accounts Admin" in roles:
            try:
                poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
            except PointOfContacts.DoesNotExist:
                return Response({"error": "You are not associated with any customer."},
                                status=status.HTTP_403_FORBIDDEN)
            if poc.belong_to_id != vin_vehicle.customer_id:
                return Response({"error": "You are not authorized to view this VIN vehicle."},
                                status=status.HTTP_403_FORBIDDEN)

        elif any(role in roles for role in ["Dispenser Manager", "Location Manager", "Dispenser"]):
            user_pocs = PointOfContacts.objects.filter(user_id=user_id, belong_to_type="delivery_location")
            if not user_pocs.exists():
                return Response({"error": "You are not associated with any delivery location."},
                                status=status.HTTP_403_FORBIDDEN)
            delivery_location_ids = [poc.belong_to_id for poc in user_pocs]
            vin_locations = vin_vehicle.delivery_location_id or []
            if not any(loc_id in vin_locations for loc_id in delivery_location_ids):
                return Response({"error": "You are not authorized to view this VIN vehicle."},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"error": "You are not authorized to view VIN vehicles."},
                            status=status.HTTP_403_FORBIDDEN)

        # ---------- 3️⃣ Serialize and Return ----------
        serializer = GetVINVehicleSerializer(vin_vehicle)
        return Response(serializer.data, status=status.HTTP_200_OK)    


class GetVINVehicleByCustomerID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        query_type = request.query_params.get("data", "all").lower()  # all | used | unused

        # ---------- 🧩 Role Validation ----------
        if not any(role in roles for role in ['IOT Admin', 'Accounts Admin', 'Dispenser Manager', 'Location Manager']):
            return Response(
                {"error": "You are not authorized to access VINs by customer ID."},
                status=status.HTTP_403_FORBIDDEN
            )

        # ---------- 🔍 Base Query ----------
        vins = VIN_Vehicle.objects.filter(customer_id=customer_id)

        if not vins.exists():
            return Response(
                {"message": f"No VIN records found for customer ID {customer_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------- 🎚️ Apply “used” or “unused” filter ----------
        if query_type == "used":
            vins = vins.filter(status=True)
        elif query_type == "unused":
            vins = vins.filter(status=False)

        # ---------- 🧾 Accounts Admin Validation ----------
        if 'Accounts Admin' in roles:
            try:
                poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
            except PointOfContacts.DoesNotExist:
                return Response(
                    {"error": "You are not associated with any customer."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if poc.belong_to_id != int(customer_id):
                return Response(
                    {"error": "You are not authorized to access this customer's VIN data."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # ---------- 🧭 Dispenser Manager / Location Manager Validation ----------
        elif any(role in roles for role in ['Dispenser Manager', 'Location Manager']):
            # Get all delivery locations assigned to this user
            user_pocs = PointOfContacts.objects.filter(user_id=user_id, belong_to_type="delivery_location")
            if not user_pocs.exists():
                return Response(
                    {"error": "You are not associated with any delivery location."},
                    status=status.HTTP_403_FORBIDDEN
                )

            delivery_location_ids = [poc.belong_to_id for poc in user_pocs]

            # Filter VINs by both customer_id and matching delivery locations
            vins = vins.filter(
                Q(delivery_location_id__contains=delivery_location_ids[0]) |
                Q(delivery_location_id__icontains=str(delivery_location_ids[0]))
            )

            # For multiple delivery locations, chain OR conditions
            if len(delivery_location_ids) > 1:
                q_filter = Q()
                for loc_id in delivery_location_ids:
                    q_filter |= Q(delivery_location_id__contains=loc_id) | Q(delivery_location_id__icontains=str(loc_id))
                vins = vins.filter(q_filter)

            if not vins.exists():
                return Response(
                    {"message": "No VIN records found for your assigned delivery locations."},
                    status=status.HTTP_404_NOT_FOUND
                )

        # ---------- ✅ Serialize and Return ----------
        serializer = GetVINVehicleSerializer(vins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class EditVINVehicle(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]
    
    def put(self, request, vin_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # ---------- 1️⃣ Fetch VIN ----------
        try:
            vin_vehicle = VIN_Vehicle.objects.get(id=vin_id)
        except VIN_Vehicle.DoesNotExist:
            return Response({"error": "VIN vehicle not found."}, status=status.HTTP_404_NOT_FOUND)

        # ---------- 2️⃣ Initialize Serializer ----------
        serializer = EditVINVehicleSerializer(
            vin_vehicle,
            data=request.data,
            partial=True,
            context={
                "user": user,
                "roles": roles,
                "vin_vehicle": vin_vehicle,
            },
        )

        # ---------- 3️⃣ Validate & Save ----------
        serializer.is_valid(raise_exception=True)
        updated_vin = serializer.save()

        return Response(
            {
                "message": "VIN vehicle updated successfully.",
            },
            status=status.HTTP_200_OK,
        )


class DeleteVINVehicle(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request, vin_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        # ---------- 1️⃣ Check VIN existence ----------
        try:
            vin_vehicle = VIN_Vehicle.objects.get(id=vin_id)
        except VIN_Vehicle.DoesNotExist:
            return Response({"error": "VIN vehicle not found."}, status=status.HTTP_404_NOT_FOUND)

        # ---------- 2️⃣ Initialize Serializer ----------
        serializer = DeleteVINVehicleSerializer(
            vin_vehicle,
            context={"user": user, "roles": roles, "vin_vehicle": vin_vehicle},
        )

        # ---------- 3️⃣ Validation ----------
        serializer.is_valid(raise_exception=True)

        # ---------- 4️⃣ Perform Hard Delete ----------
        serializer.delete(vin_vehicle)

        return Response(
            {
                "message": "VIN vehicle deleted successfully and permanently removed.",
                "vin_id": vin_id
            },
            status=status.HTTP_200_OK,
        )

        

class AddDispenserGunMappingToVehicles(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            serializer = CreateDispenserGunMappingToVehiclesSerializer(data=request.data, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Dispenser & Gun Unit Mapping to Vehicles Created Successfully",
                    }, status=status.HTTP_201_CREATED)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to add a dispenser gun mapping to vehicles"}, status=status.HTTP_403_FORBIDDEN)


#Get Dispenser Gun Mapping to Customer
class GetDispenserGunMappingToVehicles(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            dispenser_gun_mapping_to_vehicles = Dispenser_Gun_Mapping_To_Vehicles.objects.all()
            serializer = GetDispenserGunMappingToVehiclesSerializer(dispenser_gun_mapping_to_vehicles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get dispenser gun mapping to vehicles"}, status=status.HTTP_403_FORBIDDEN)



#Get Dispenser Gun Mapping to Vehicles by Vehicle ID
class GetDispenserGunMappingToVehiclesByID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        dispenser_gun_mapping_to_vehicles = Dispenser_Gun_Mapping_To_Vehicles.objects.get(id=id)
            
        serializer = GetDispenserGunMappingToVehiclesSerializer(dispenser_gun_mapping_to_vehicles)
        return Response(serializer.data, status=status.HTTP_200_OK)


#Get Dispenser Gun Mapping to Vehicles by Vehicle ID
class GetDispenserGunMappingToVehiclesByVehicleID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, vehicle_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        dispenser_gun_mapping_to_vehicles = Dispenser_Gun_Mapping_To_Vehicles.objects.filter(
                    vehicle=vehicle_id,
                    assigned_status=True
                )
            
        serializer = GetDispenserGunMappingToVehiclesSerializer(dispenser_gun_mapping_to_vehicles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class GetDispenserGunMappingByVehicleNo(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        serializer = VehicleNoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vehicle_no = serializer.validated_data["vehicle_no"]

        # Step 1: Get vehicle
        vehicle = Vehicles.objects.filter(
            vehicle_no=vehicle_no,
            deleted_at__isnull=True
        ).first()

        if not vehicle:
            return Response(
                {"error": "Vehicle not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 2: Get dispenser-gun mappings
        mappings = Dispenser_Gun_Mapping_To_Vehicles.objects.filter(
            vehicle=vehicle.id,
            assigned_status=True
        )

        # Step 3: Serialize response
        response_serializer = GetDispenserGunMappingToVehiclesSerializer(
            mappings, many=True
        )

        return Response(
            {
                "vehicle_id": vehicle.id,
                "vehicle_no": vehicle.vehicle_no,
                "mappings": response_serializer.data
            },
            status=status.HTTP_200_OK
        )



#Edit Dispenser Gun Mapping to Vehicles
class EditDispenserGunMappingToVehicles(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            try:
                instance = Dispenser_Gun_Mapping_To_Vehicles.objects.get(id=id)
            except Dispenser_Gun_Mapping_To_Vehicles.DoesNotExist:
                return Response({'error': 'Dispenser Gun Mapping To Vehicles with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = EditDispenserGunMappingToVehiclesSerializer(instance, data=request.data, partial=True, context={"user": user})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.save()
                    return Response({
                        "message": "Dispenser Gun Mapping to Vehicles Updated Successfully",
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to edit a dispenser gun mapping to vehicle"}, status=status.HTTP_403_FORBIDDEN)

class EditStatusAndAssignedStatusOfDispenserGunMappingToVehicles(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        
        if "IOT Admin" in roles:
            try:
                instance = Dispenser_Gun_Mapping_To_Vehicles.objects.get(id=id)
            except Dispenser_Gun_Mapping_To_Vehicles.DoesNotExist:
                return Response({'error': 'Dispenser Gun Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = EditStatusAndAssignedStatusOfDispenserGunMappingToVehiclesSerializer(instance, data=request.data, partial=True, context={"user": user})
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
            return Response({"error": "You are not authorized to edit the status of a dispenser gun mapping to vehicles"}, status=status.HTTP_403_FORBIDDEN)

#Delete Dispenser Gun Mapping to Vehicles
class DeleteDispenserGunMappingToVehicles(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if "IOT Admin" in roles:
            try:
                instance = Dispenser_Gun_Mapping_To_Vehicles.objects.get(id=id)
            except Dispenser_Gun_Mapping_To_Vehicles.DoesNotExist:
                return Response({'error': 'Dispenser Gun Mapping with this ID not found'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = DeleteDispenserGunMappingToVehiclesSerializer(data={'id': id}, context={'instance': instance})
            if serializer.is_valid(raise_exception=True):
                try:
                    serializer.delete(instance)
                    return Response({'message': 'Dispenser Gun Mapping to Vehicles Deleted Successfully'}, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "You are not authorized to delete a dispenser gun mapping to vehicles"}, status=status.HTTP_403_FORBIDDEN)




class CreateOrderRequestForFuelDispensing(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        print(user_id)

        try:
            serializer = CreateRequestForOrderFuelDispensingSerializer(
                data=request.data,
                context={"roles": roles, "user": user}
            )
            if serializer.is_valid(raise_exception=True):
                try:
                    response_data = serializer.save()
                    return Response({
                        "message": "Fuel dispensing order request created successfully.",
                        "data": {"transaction_id": response_data.get("transaction_id")}
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    print("error", e)
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class GetOrderFuelDispensingRequests(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        if "IOT Admin" not in roles:
            return Response(
                {"error": "You are not authorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = OrderFuelDispensingDetails.objects.all().order_by("-id")

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrderFuelDispensingRequestsById(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.get(
                id=id
            )
        serializer = GetOrderFuelDispensingDetailsSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)



class GetOrderFuelDispensingRequestsByVehicleId(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, vehicle_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.filter(
                vehicle_id=vehicle_id
            ).order_by("-id")
        if not queryset.exists():
            return Response(
                {"error": "Order Fuel Dispensing Details not found for this vehicle"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrderFuelDispensingRequestsByDriverId(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, driver_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.filter(
                driver_id=driver_id
            ).order_by("-id")
        if not queryset.exists():
            return Response(
                {"error": "Order Fuel Dispensing Details not found for this driver"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetOrderFuelDispensingRequestsByCustomerId(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.filter(
                customer_id=customer_id
            ).order_by("-id")
        if not queryset.exists():
            return Response(
                {"error": "Order Fuel Dispensing Details not found for this customer"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrderFuelDispensingRequestsByRoutePlanId(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, route_plan_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.filter(
                route_plan_id=route_plan_id
            ).order_by("-id")
        if not queryset.exists():
            return Response(
                {"error": "Order Fuel Dispensing Details not found for this route plan"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrderFuelDispensingRequestsByRoutePlanDetailsId(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, route_plan_details_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.filter(
                route_plan_details_id=route_plan_details_id
            ).order_by("-id")
        if not queryset.exists():
            return Response(
                {"error": "Order Fuel Dispensing Details not found for this route plan"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetOrderFuelDispensingRequestsByOrderId(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)

        queryset = OrderFuelDispensingDetails.objects.filter(
                order_id=order_id
            ).order_by("-id")
        if not queryset.exists():
            return Response(
                {"error": "Order Fuel Dispensing Details not found for this order"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetOrderFuelDispensingDetailsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

