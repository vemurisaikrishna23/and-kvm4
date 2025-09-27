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