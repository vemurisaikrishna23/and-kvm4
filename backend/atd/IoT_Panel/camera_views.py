"""
Camera management APIs. Design: ATD_Server/CAMERA_MANAGEMENT_DESIGN.md (section 7).
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from existing_tables.models import PointOfContacts
from . import mediamtx, app_logs, log_presence, camera_service, mediamtx_logs
from .camera_serializers import (
    CameraEventSerializer,
    CameraSerializer,
    CameraStreamSessionSerializer,
    RequestCameraSnapshotSerializer,
    current_assignment,
)
from .mediamtx import MediaMTXError
from .models import Camera, CameraEvent, CameraStreamSession, DispenserUnits, OrderFuelDispensingDetails, RequestCameraSnapshot, RequestFuelDispensingDetails
from .renderers import IoT_PanelRenderer
from .views import FuelDispensingPagination, get_user_roles, is_customer_point_of_contact

IOT_ADMIN = "IOT Admin"
REQUEST_VIEW_ROLES = ["IOT Admin", "Accounts Admin", "Dispenser Manager", "Location Manager", "Dispenser"]


def _user(request):
    user_id = getattr(request.user, "id", None)
    return user_id, get_user_roles(user_id)


def _forbidden(msg="You are not authorized to perform this action."):
    return Response({"error": msg}, status=status.HTTP_403_FORBIDDEN)


def _not_found(msg="Camera not found."):
    return Response({"error": msg}, status=status.HTTP_404_NOT_FOUND)


def _get_camera(id):
    return Camera.objects.select_related("dispenser_unit").filter(id=id).first()


def can_view_camera(user_id, roles, camera):
    if IOT_ADMIN in roles:
        return True

    a = current_assignment(camera.dispenser_unit_id)
    if not a:
        return False

    # Assigned to a customer: the customer's points of contact may watch it.
    if a.get("customer_id"):
        return is_customer_point_of_contact(user_id, a["customer_id"])

    # Assigned to a vehicle (the route-plan flow). current_assignment returns no
    # customer_id in that case, so the clause above used to reject everyone but
    # IOT Admin -- a driver could not open the camera of the dispenser on their
    # own vehicle. Scope it to exactly that: the driver who raised a fuel
    # request on this vehicle, and nobody else.
    if a.get("vehicle_id") and user_id is not None:
        return OrderFuelDispensingDetails.objects.filter(
            vehicle_id=a["vehicle_id"], driver_id=user_id
        ).exists()

    return False


def can_view_request(user_id, roles, req):
    """Same rule as GetFuelDispensingRequestsByID."""
    if not any(r in roles for r in REQUEST_VIEW_ROLES):
        return False
    if "Accounts Admin" in roles and IOT_ADMIN not in roles:
        poc = PointOfContacts.objects.filter(user_id=user_id, belong_to_type="customer").first()
        return bool(poc and req.customer_id == poc.belong_to_id)
    return True


def can_view_order_request(user_id, roles, order):
    """
    Who may see an order request's snapshots (the route-plan / vehicle flow).

    can_view_request is not reusable here: it gates on REQUEST_VIEW_ROLES, which
    does not include "Driver" -- the only role the drivers who raise these
    requests actually hold -- so it rejects the people the screen is built for.
    Scope it to the request's own driver instead, plus IOT Admin and the
    customer's points of contact.
    """
    if IOT_ADMIN in roles:
        return True
    if user_id is None:
        return False
    if order.driver_id and order.driver_id == user_id:
        return True
    if order.customer_id:
        return is_customer_point_of_contact(user_id, order.customer_id)
    return False


def _with_live(data_list, cameras):
    live = camera_service.live_status_map(cameras)
    by_id = {c.id: c for c in cameras}
    for item in data_list:
        st = live.get(item["id"], {"live_status": "unknown", "live": None})
        item["live_status"] = st["live_status"]
        item["live"] = st["live"]
        cam = by_id.get(item["id"])
        item["active_sessions"] = camera_service.active_sessions(cam).count() if cam else 0
        item["enabled"] = st["live_status"] in ("live", "waiting")
    return data_list


# --- CRUD (IOT Admin) ----------------------------------------------------------

class AddCamera(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden("You are not authorized to add a camera.")
        serializer = CameraSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        camera = serializer.save()
        camera_service.log_event(camera, "camera_created", {"rtmp_path": camera.rtmp_path}, user_id)
        camera_service.on_camera_saved(camera, user_id=user_id)
        return Response({"message": "Camera added successfully", "data": CameraSerializer(camera).data}, status=status.HTTP_201_CREATED)


class GetCameras(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        qs = Camera.objects.select_related("dispenser_unit").order_by("-id")
        p = request.query_params
        if p.get("dispenser_unit_id"):
            qs = qs.filter(dispenser_unit_id=p["dispenser_unit_id"])
        if p.get("is_active") in ("true", "false"):
            qs = qs.filter(is_active=p["is_active"] == "true")
        if p.get("search"):
            s = p["search"]
            qs = qs.filter(
                Q(serial_number__icontains=s) | Q(model_number__icontains=s) | Q(rtmp_path__icontains=s)
                | Q(dispenser_unit__serial_number__icontains=s) | Q(dispenser_unit__imei_number__icontains=s)
            )
        cameras = list(qs)
        data = CameraSerializer(cameras, many=True).data
        if p.get("customer_id"):
            data = [d for d in data if (d.get("assignment") or {}).get("customer_id") == int(p["customer_id"])]
            cameras = [c for c in cameras if c.id in {d["id"] for d in data}]
        if p.get("live", "true") != "false":
            data = _with_live(list(data), cameras)
        return Response(data, status=status.HTTP_200_OK)


class GetCameraByID(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user_id, roles = _user(request)
        camera = _get_camera(id)
        if camera is None:
            return _not_found()
        if not can_view_camera(user_id, roles, camera):
            return _forbidden()
        return Response(_with_live([CameraSerializer(camera).data], [camera])[0], status=status.HTTP_200_OK)


class GetCamerasByDispenser(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, dispenser_unit_id, format=None):
        user_id, roles = _user(request)
        cameras = list(Camera.objects.select_related("dispenser_unit").filter(dispenser_unit_id=dispenser_unit_id).order_by("id"))
        if not cameras:
            return Response([], status=status.HTTP_200_OK)
        if not can_view_camera(user_id, roles, cameras[0]):
            return _forbidden()
        data = CameraSerializer(cameras, many=True).data
        if request.query_params.get("live", "false") == "true":
            data = _with_live(list(data), cameras)
        return Response(data, status=status.HTTP_200_OK)



class GetCamerasByDispenserIMEI(APIView):
    """Cameras of the dispenser with this IMEI (request screens only know the IMEI)."""
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, imei, format=None):
        du = DispenserUnits.objects.filter(imei_number=str(imei)).first()
        if du is None:
            return Response([], status=status.HTTP_200_OK)
        return GetCamerasByDispenser().get(request, du.id)

class EditCamera(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def put(self, request, id, format=None):
        return self._edit(request, id, partial=False)

    def patch(self, request, id, format=None):
        return self._edit(request, id, partial=True)

    def _edit(self, request, id, partial):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden("You are not authorized to edit a camera.")
        camera = _get_camera(id)
        if camera is None:
            return _not_found()
        old_path = camera.rtmp_path
        serializer = CameraSerializer(camera, data=request.data, partial=partial, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        camera = serializer.save()
        if old_path != camera.rtmp_path:
            camera_service.end_all_sessions(camera, "camera_edited", user_id=user_id)
        camera_service.log_event(camera, "camera_updated", {"changes": list(request.data.keys()), "old_rtmp_path": old_path, "rtmp_path": camera.rtmp_path}, user_id)
        camera_service.on_camera_saved(camera, old_rtmp_path=old_path, user_id=user_id)
        return Response({"message": "Camera updated successfully", "data": CameraSerializer(camera).data}, status=status.HTTP_200_OK)


class DeleteCamera(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden("You are not authorized to delete a camera.")
        camera = _get_camera(id)
        if camera is None:
            return _not_found()
        camera_service.on_camera_deleting(camera, user_id=user_id)
        camera_service.log_event(None, "camera_deleted", {"camera_id": camera.id, "serial_number": camera.serial_number, "rtmp_path": camera.rtmp_path}, user_id)
        camera.delete()
        return Response({"message": "Camera deleted successfully"}, status=status.HTTP_200_OK)


# --- control & monitoring (IOT Admin) --------------------------------------------

class CameraStatus(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user_id, roles = _user(request)
        camera = _get_camera(id)
        if camera is None:
            return _not_found()
        if not can_view_camera(user_id, roles, camera):
            return _forbidden()
        data = camera_service.camera_status(camera)
        data.update({"id": camera.id, "rtmp_path": camera.rtmp_path, "stream_mode": camera.stream_mode, "is_active": camera.is_active})
        return Response(data, status=status.HTTP_200_OK)


class EnableCamera(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        camera = _get_camera(id)
        if camera is None:
            return _not_found()
        if not camera.is_active or camera.stream_mode == camera_service.STREAM_MODE_DISABLED:
            return Response({"error": "Camera is inactive or its stream mode is Disabled."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            minutes = int(request.data.get("minutes", 15))
        except (TypeError, ValueError):
            return Response({"error": "minutes must be a number."}, status=status.HTTP_400_BAD_REQUEST)
        minutes = max(1, min(minutes, 24 * 60))
        s = camera_service.start_session(camera, "manual", minutes * 60, user_id=user_id)
        return Response({"message": f"Camera enabled for {minutes} minutes", "session_id": s.id, "expires_at": s.expires_at}, status=status.HTTP_200_OK)


class DisableCamera(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        camera = _get_camera(id)
        if camera is None:
            return _not_found()
        camera_service.end_all_sessions(camera, "manual_disable", user_id=user_id)
        ok = camera_service.reconcile_camera(camera)
        msg = "Camera disabled" if ok else "Sessions ended, but MediaMTX could not be reached; it will be disabled on the next sync."
        if camera.stream_mode == camera_service.STREAM_MODE_ALWAYS_ON:
            msg = "Sessions ended. Camera stream mode is Always On, so it stays enabled; change the mode to stop it."
        return Response({"message": msg}, status=status.HTTP_200_OK)


def _date_filter(qs, request, field):
    for param, lookup in (("from", "gte"), ("to", "lte")):
        v = request.query_params.get(param)
        if v:
            dt = parse_datetime(v)
            if dt is not None:
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                qs = qs.filter(**{f"{field}__{lookup}": dt})
    return qs


class CameraLogs(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        if not Camera.objects.filter(id=id).exists():
            return _not_found()
        qs = CameraEvent.objects.filter(camera_id=id).order_by("-created_at")
        if request.query_params.get("event"):
            qs = qs.filter(event=request.query_params["event"])
        qs = _date_filter(qs, request, "created_at")
        paginator = FuelDispensingPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(CameraEventSerializer(page, many=True).data)


class CameraSessions(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, id, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        if not Camera.objects.filter(id=id).exists():
            return _not_found()
        qs = _date_filter(CameraStreamSession.objects.filter(camera_id=id).order_by("-started_at"), request, "started_at")
        paginator = FuelDispensingPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(CameraStreamSessionSerializer(page, many=True).data)


class RTMPDevices(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        try:
            conns = mediamtx.list_rtmp_conns()
        except MediaMTXError as e:
            return Response({"error": f"MediaMTX unreachable: {e}"}, status=status.HTTP_502_BAD_GATEWAY)
        cameras = {c.rtmp_path: c for c in Camera.objects.select_related("dispenser_unit")}
        data = []
        for c in conns:
            cam = cameras.get(c.get("path"))
            ident = mediamtx_logs.decode_rtmp_path(c.get("path"), cameras) or {}
            data.append({
                "model_number": ident.get("model_number"),
                "serial_number": ident.get("serial_number"),
                "identity_source": ident.get("source"),
                "id": c.get("id"),
                "remote_addr": c.get("remoteAddr"),
                "path": c.get("path"),
                "state": c.get("state"),
                "created": c.get("created"),
                "bytes_received": c.get("bytesReceived"),
                "bytes_sent": c.get("bytesSent"),
                "registered": cam is not None,
                "camera_id": cam.id if cam else None,
                "camera_serial_number": cam.serial_number if cam else None,
                "dispenser_serial_number": cam.dispenser_unit.serial_number if cam else None,
            })
        return Response(data, status=status.HTTP_200_OK)


class MediaMTXHealth(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        worker = camera_service.worker_status()
        try:
            data = mediamtx.health()
            configured = set(mediamtx.list_config_paths())
        except MediaMTXError as e:
            return Response({"reachable": False, "error": str(e), **worker}, status=status.HTTP_200_OK)
        managed = set(Camera.objects.values_list("rtmp_path", flat=True))
        data.update(worker)
        data.update({
            "configured_paths": len(configured),
            "managed_cameras": len(managed),
            "managed_enabled": len(managed & configured),
        })
        return Response(data, status=status.HTTP_200_OK)


# --- live view (IOT Admin or customer point of contact) ------------------------------

class LiveStart(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, camera_id, format=None):
        user_id, roles = _user(request)
        camera = _get_camera(camera_id)
        if camera is None:
            return _not_found()
        if not can_view_camera(user_id, roles, camera):
            return _forbidden("You are not authorized to view this camera.")
        if not camera.is_active or camera.stream_mode == camera_service.STREAM_MODE_DISABLED:
            return Response({"error": "Camera is inactive or disabled."}, status=status.HTTP_400_BAD_REQUEST)
        s = camera_service.start_session(camera, "live_view", settings.CAMERA_LIVE_TTL_S, user_id=user_id)
        st = camera_service.live_status_map([camera])[camera.id]
        return Response({
            "session_id": s.id,
            "camera_id": camera.id,
            "webrtc_url": camera.webrtc_url,
            "expires_in": settings.CAMERA_LIVE_TTL_S,
            "heartbeat_every": max(5, settings.CAMERA_LIVE_TTL_S // 3),
            "live_status": st["live_status"],
            "camera_live": st["live_status"] == "live",
        }, status=status.HTTP_200_OK)


def _own_live_session(request, session_id):
    user_id, roles = _user(request)
    s = CameraStreamSession.objects.select_related("camera").filter(id=session_id, reason="live_view").first()
    if s is None:
        return None, _not_found("Session not found.")
    if s.user_id != user_id and IOT_ADMIN not in roles:
        return None, _forbidden()
    return s, None


class LiveHeartbeat(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, format=None):
        s, err = _own_live_session(request, session_id)
        if err:
            return err
        if s.ended_at is not None or s.expires_at <= timezone.now():
            # Expired (e.g. laptop slept): tell the client to start a new session.
            return Response({"error": "Session ended.", "ended": True}, status=status.HTTP_410_GONE)
        camera_service.heartbeat(s, settings.CAMERA_LIVE_TTL_S)
        st = camera_service.live_status_map([s.camera])[s.camera_id]
        return Response({
            "expires_in": settings.CAMERA_LIVE_TTL_S,
            "live_status": st["live_status"],
            "camera_live": st["live_status"] == "live",
        }, status=status.HTTP_200_OK)


class LiveStop(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, format=None):
        s, err = _own_live_session(request, session_id)
        if err:
            return err
        camera_service.end_session(s, "closed", user_id=getattr(request.user, "id", None))
        return Response({"message": "Live view closed"}, status=status.HTTP_200_OK)


# --- request snapshots -------------------------------------------------------------------

def request_camera_state(req):
    """Why a request does / doesn't have snapshots: camera on its dispenser? session on? camera live?"""
    du = DispenserUnits.objects.filter(imei_number=req.dispenser_imeinumber).first()
    cams = list(Camera.objects.filter(dispenser_unit=du).order_by("id")) if du else []
    state = {
        "dispenser_serial_number": req.dispenser_serialnumber,
        "dispenser_imei": req.dispenser_imeinumber,
        "has_camera": bool(cams),
        "camera_serial_numbers": [c.serial_number for c in cams],
        "session_active": camera_service.active_sessions()
        .filter(reason="fuel_request", transaction_id=req.transaction_id)
        .exists(),
        "live_status": None,
    }
    if cams and req.request_status not in camera_service.FINAL_STATUS_END_REASON:
        state["live_status"] = camera_service.live_status_map(cams)[cams[0].id]["live_status"]
    return state


class GetRequestSnapshots(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id, format=None):
        user_id, roles = _user(request)
        req = RequestFuelDispensingDetails.objects.filter(id=request_id).first()
        if req is None:
            return _not_found("Fuel Dispensing Request ID not found.")
        if not can_view_request(user_id, roles, req):
            return _forbidden("You are not authorized to access this data.")
        qs = RequestCameraSnapshot.objects.filter(request=req).order_by("captured_at")
        if request.query_params.get("kind") in ("periodic", "stage"):
            qs = qs.filter(kind=request.query_params["kind"])
        return Response({
            "request_id": req.id,
            "transaction_id": req.transaction_id,
            "request_status": req.request_status,
            "snapshot_count": req.snapshot_count,
            "latest_snapshot_path": req.latest_snapshot_path,
            "snapshots": RequestCameraSnapshotSerializer(qs, many=True).data,
            "camera_state": request_camera_state(req),
        }, status=status.HTTP_200_OK)


class GetOrderRequestSnapshots(APIView):
    """Snapshots of an order request (route-plan flow).

    RequestCameraSnapshot carries both a `request` and an `order_request` FK and
    the camera worker stamps whichever applies, but GetRequestSnapshots only
    ever looked in RequestFuelDispensingDetails -- so order requests had no way
    to read the snapshots that were being captured for them.
    """

    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id, format=None):
        user_id, roles = _user(request)
        order = OrderFuelDispensingDetails.objects.filter(id=request_id).first()
        if order is None:
            return _not_found("Order Fuel Dispensing Request ID not found.")
        if not can_view_order_request(user_id, roles, order):
            return _forbidden("You are not authorized to access this data.")
        qs = RequestCameraSnapshot.objects.filter(order_request=order).order_by("captured_at")
        if request.query_params.get("kind") in ("periodic", "stage"):
            qs = qs.filter(kind=request.query_params["kind"])
        snapshots = RequestCameraSnapshotSerializer(qs, many=True).data
        latest = qs.last()
        return Response({
            "request_id": order.id,
            "transaction_id": order.transaction_id,
            "request_status": order.request_status,
            # This table has no denormalised snapshot_count / latest_snapshot_path
            # columns, so both are derived from the rows themselves.
            "snapshot_count": len(snapshots),
            "latest_snapshot_path": getattr(latest, "image_path", None),
            "snapshots": snapshots,
            "camera_state": request_camera_state(order),
        }, status=status.HTTP_200_OK)


class GetLatestRequestSnapshot(APIView):
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id, format=None):
        user_id, roles = _user(request)
        req = RequestFuelDispensingDetails.objects.filter(id=request_id).first()
        if req is None:
            return _not_found("Fuel Dispensing Request ID not found.")
        if not can_view_request(user_id, roles, req):
            return _forbidden("You are not authorized to access this data.")
        latest = RequestCameraSnapshot.objects.filter(request=req).order_by("-captured_at").first()
        return Response({
            "request_id": req.id,
            "transaction_id": req.transaction_id,
            "request_status": req.request_status,
            "snapshot_count": req.snapshot_count,
            "snapshot": RequestCameraSnapshotSerializer(latest).data if latest else None,
            "camera_state": request_camera_state(req),
        }, status=status.HTTP_200_OK)


# --- live MediaMTX log (same lines as `docker logs mediamtx-server`) -------------------------

LOG_SCOPES = ("cameras", "errors", "all")


class MediaMTXLogs(APIView):
    """GET camera/mediamtx/logs/?cursor=<c>&scope=cameras|errors|all&q=<text>&lines=300

    First call (no cursor) returns the last `lines` lines; then pass back `cursor`
    every ~2 s to get only new lines. Each line is parsed (time, level, component,
    conn/ip, path) and enriched with the camera identity for its path."""
    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden()
        p = request.query_params
        scope = p.get("scope", "cameras")
        if scope not in LOG_SCOPES:
            scope = "cameras"
        q = (p.get("q") or "").strip().lower()
        try:
            initial = max(10, min(int(p.get("lines", 300)), 2000))
        except ValueError:
            initial = 300
        try:
            raw, cursor, rotated = mediamtx_logs.read(p.get("cursor") or None, initial_lines=initial)
        except mediamtx_logs.LogsUnavailable as e:
            return Response({"available": False, "error": str(e), "lines": [], "cursor": None}, status=status.HTTP_200_OK)
        except OSError as e:
            return Response({"available": False, "error": f"Cannot read MediaMTX log: {e}", "lines": [], "cursor": None}, status=status.HTTP_200_OK)

        cameras = {c.rtmp_path: c for c in Camera.objects.select_related("dispenser_unit")}
        conn_paths = {}
        out = []
        for line in raw:
            e = mediamtx_logs.parse_line(line)
            if e is None:
                continue
            # remember which path a connection belongs to (RTMP "opened"/"closed" lines carry no path)
            if e["conn"] and e["path"]:
                conn_paths[e["conn"]] = e["path"]
            elif e["conn"] and not e["path"] and e["conn"] in conn_paths:
                e["path"] = conn_paths[e["conn"]]
            if scope == "errors" and e["level"] not in ("ERR", "WAR"):
                continue
            if scope == "cameras":
                is_camera = e["component"] in ("RTMP", "WebRTC", "HLS") or (
                    e["path"] and (e["path"] in cameras or e["path"].startswith("rtmp_push"))
                )
                if not is_camera:
                    continue
            if q and q not in e["text"].lower():
                continue
            e["camera"] = mediamtx_logs.decode_rtmp_path(e["path"], cameras)
            out.append(e)
        return Response({
            "available": True,
            "cursor": cursor,
            "rotated": rotated,
            "scope": scope,
            "lines": out,
            "conn_paths": conn_paths,
        }, status=status.HTTP_200_OK)


class AppLogs(APIView):
    """GET api/app-logs/?cursor=<c>&level=all|error|warning&q=<text>&lines=300

    The backend's own log, for the IoT Admin ("super admin") live viewer. Same
    cursor contract as MediaMTXLogs: the first call returns the last `lines`
    lines, then the caller passes `cursor` back every couple of seconds and gets
    only what is new. `rotated` tells the client its view was replaced rather
    than appended to.

    Lines are redacted in app_logs.redact before they leave the server -- a
    console is not a safe place to publish tokens from.
    """

    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden("You are not authorized to read the server log.")

        # Someone is watching: this is what turns the verbose logging on.
        log_presence.touch()

        p = request.query_params
        level = (p.get("level") or "all").lower()
        q = (p.get("q") or "").strip().lower()
        try:
            initial = max(10, min(int(p.get("lines", app_logs.DEFAULT_LINES)), app_logs.MAX_LINES))
        except ValueError:
            initial = app_logs.DEFAULT_LINES

        try:
            raw, cursor, rotated = app_logs.read(p.get("cursor") or None, initial_lines=initial)
        except app_logs.LogsUnavailable as e:
            return Response(
                {"available": False, "error": str(e), "lines": [], "cursor": None, "rotated": False},
                status=status.HTTP_200_OK,
            )
        except OSError as e:
            return Response(
                {
                    "available": False,
                    "error": f"Cannot read the server log: {e}",
                    "lines": [],
                    "cursor": None,
                    "rotated": False,
                },
                status=status.HTTP_200_OK,
            )

        wanted = {"error": {"ERROR"}, "warning": {"ERROR", "WARNING"}}.get(level)
        out = []
        for line in raw:
            entry = app_logs.parse_line(line)
            if entry is None:
                continue
            if wanted and entry["level"] not in wanted:
                continue
            if q and q not in entry["raw"].lower():
                continue
            out.append(entry)

        return Response(
            {
                "available": True,
                "lines": out,
                "cursor": cursor,
                "rotated": rotated,
                "file": app_logs.log_path(),
            },
            status=status.HTTP_200_OK,
        )


class ClearAppLogs(APIView):
    """POST api/app-logs/clear/ -- empty the server log file.

    Destructive and IoT Admin only. The file is truncated rather than deleted so
    the running server's open descriptors keep working, and the clear itself is
    logged immediately afterwards so the fresh file records who emptied it.
    """

    renderer_classes = [IoT_PanelRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user_id, roles = _user(request)
        if IOT_ADMIN not in roles:
            return _forbidden("You are not authorized to clear the server log.")
        try:
            cursor = app_logs.truncate()
        except app_logs.LogsUnavailable as e:
            return Response({"cleared": False, "error": str(e)}, status=status.HTTP_200_OK)
        except OSError as e:
            return Response(
                {"cleared": False, "error": f"Cannot clear the server log: {e}"},
                status=status.HTTP_200_OK,
            )

        # First line of the new file: an audit trail for a destructive action.
        logging.getLogger("IoT_Panel").warning("Server log cleared by user_id=%s", user_id)
        return Response({"cleared": True, "cursor": cursor}, status=status.HTTP_200_OK)
