"""IoT Admin dashboard API (other roles keep their existing dashboards)."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import dashboard_iot_admin
from .renderers import IoT_PanelRenderer
from .views import get_user_roles


class IoTAdminDashboard(APIView):
    """GET dashboard/iot-admin/?from=YYYY-MM-DD&to=YYYY-MM-DD  (IST, inclusive; default last 30 days)"""
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        roles = get_user_roles(getattr(request.user, "id", None))
        if "IOT Admin" not in roles:
            return Response({"error": "Only IOT Admin can view this dashboard."}, status=status.HTTP_403_FORBIDDEN)
        try:
            d_from, d_to = dashboard_iot_admin.parse_range(request.query_params.get("from"), request.query_params.get("to"))
        except dashboard_iot_admin.RangeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(dashboard_iot_admin.build(d_from, d_to), status=status.HTTP_200_OK)
