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
from django.db.models import Q


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
                        "data": {"transaction_id": response_data.transaction_id}
                    }, status=status.HTTP_200_OK)
                except serializers.ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
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
            fuel_dispensing_requests = RequestFuelDispensingDetails.objects.all()
            serializer = GetFuelDispensingRequestsSerializer(fuel_dispensing_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to get fuel dispensing requests"}, status=status.HTTP_403_FORBIDDEN)


#Get Fuel Dispensing Requests by Customer ID
class GetFuelDispensingRequestsByCustomerID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):

            if 'Accounts Admin' in roles:
                # Accounts Admin can fetch only their associated customer's data
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
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

            # Passed validation
            fuel_dispensing_requests = RequestFuelDispensingDetails.objects.filter(customer_id=customer_id)
            serializer = GetFuelDispensingRequestsSerializer(fuel_dispensing_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(
                {"error": "You are not authorized to get fuel dispensing requests."},
                status=status.HTTP_403_FORBIDDEN
            )


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
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                if dispenser_mapping.customer != poc.belong_to_id:
                    return Response({"error": "You are not authorized to access this dispenser's data."}, status=status.HTTP_403_FORBIDDEN)

            requests = RequestFuelDispensingDetails.objects.filter(dispenser_gun_mapping_id=dispenser_gun_mapping_id)
            serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)


#Get Fuel Dispensing Requests by Delivery Location ID
class GetFuelDispensingRequestsByDeliveryLocationID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, delivery_location_id, format=None):
        user = request.user
        user_id = getattr(user, "id", None)
        roles = get_user_roles(user_id)
        try:
            delivery_location = DeliveryLocations.objects.get(id=delivery_location_id)
        except DeliveryLocations.DoesNotExist:
            return Response({"error": "Delivery Location ID not found."}, status=status.HTTP_404_NOT_FOUND)
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                if delivery_location.customer_id != poc.belong_to_id:
                    return Response({"error": "You are not authorized to access this dispenser's data."}, status=status.HTTP_403_FORBIDDEN)

            requests = RequestFuelDispensingDetails.objects.filter(delivery_location_id=delivery_location_id)
            serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not authorized to access this data."}, status=status.HTTP_403_FORBIDDEN)


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
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                if asset.customer_id != poc.belong_to_id:
                    return Response({"error": "You are not authorized to access this asset's data."}, status=status.HTTP_403_FORBIDDEN)

            requests = RequestFuelDispensingDetails.objects.filter(asset_id=asset_id)
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

        try:
            request_obj = RequestFuelDispensingDetails.objects.get(id=id)
        except RequestFuelDispensingDetails.DoesNotExist:
            return Response({"error": "Fuel Dispensing Request ID not found."}, status=status.HTTP_404_NOT_FOUND)

        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):

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
        if any(role in roles for role in ['IOT Admin', 'Accounts Admin']):
            if 'Accounts Admin' in roles:
                try:
                    poc = PointOfContacts.objects.get(user_id=login_user_id, belong_to_type="customer")
                except PointOfContacts.DoesNotExist:
                    return Response({"error": "You are not associated with any customer."}, status=status.HTTP_403_FORBIDDEN)

                target_poc = PointOfContacts.objects.filter(user_id=user_id, belong_to_type="customer", belong_to_id=poc.belong_to_id).first()
                if not target_poc:
                    return Response({"error": "This user does not belong to your customer."}, status=status.HTTP_403_FORBIDDEN)

            # Valid: same customer
            requests = RequestFuelDispensingDetails.objects.filter(user_id=user_id)
            serializer = GetFuelDispensingRequestsSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # For all other roles – deny
        return Response({"error": "You are not authorized to view fuel dispensing requests."}, status=status.HTTP_403_FORBIDDEN)
