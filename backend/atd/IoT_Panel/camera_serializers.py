from django.utils import timezone
from rest_framework import serializers

from existing_tables.models import Customers
from .models import (
    Camera,
    CameraEvent,
    CameraStreamSession,
    Dispenser_Gun_Mapping_To_Customer,
    Dispenser_Gun_Mapping_To_Vehicles,
    RequestCameraSnapshot,
)
from . import camera_service


def current_assignment(dispenser_unit_id):
    """Where the dispenser is assigned right now: customer mapping first, then vehicle."""
    m = (
        Dispenser_Gun_Mapping_To_Customer.objects.filter(dispenser_unit_id=dispenser_unit_id, assigned_status=True)
        .order_by("-id")
        .values("id", "customer")
        .first()
    )
    if m:
        name = Customers.objects.filter(id=m["customer"]).values_list("name", flat=True).first()
        return {"type": "customer", "mapping_id": m["id"], "customer_id": m["customer"], "customer_name": name}
    v = (
        Dispenser_Gun_Mapping_To_Vehicles.objects.filter(dispenser_unit_id=dispenser_unit_id, assigned_status=True)
        .order_by("-id")
        .values("id", "vehicle")
        .first()
    )
    if v:
        return {"type": "vehicle", "mapping_id": v["id"], "vehicle_id": v["vehicle"]}
    return None


class CameraSerializer(serializers.ModelSerializer):
    # Optional: generated from model + serial when blank (camera_service.generate_rtmp_path).
    # Declared explicitly, so uniqueness is checked in validate() after generation.
    rtmp_path = serializers.CharField(max_length=150, required=False, allow_blank=True)
    webrtc_url = serializers.CharField(max_length=255, required=False, allow_blank=True)
    dispenser_serial_number = serializers.CharField(source="dispenser_unit.serial_number", read_only=True)
    dispenser_imei_number = serializers.CharField(source="dispenser_unit.imei_number", read_only=True)
    rtmp_publish_url = serializers.SerializerMethodField()
    assignment = serializers.SerializerMethodField()

    class Meta:
        model = Camera
        fields = [
            "id", "dispenser_unit", "dispenser_serial_number", "dispenser_imei_number", "assignment",
            "serial_number", "model_number", "brand",
            "rtmp_path", "rtmp_publish_url", "webrtc_url",
            "stream_mode", "is_active", "remarks",
            "created_at", "updated_at", "created_by", "updated_by",
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]

    def get_rtmp_publish_url(self, obj):
        return camera_service.rtmp_publish_url(obj)

    def get_assignment(self, obj):
        return current_assignment(obj.dispenser_unit_id)

    def validate_serial_number(self, value):
        return (value or "").strip().upper()

    def validate_model_number(self, value):
        return (value or "").strip().upper()

    def validate_rtmp_path(self, value):
        if not (value or "").strip():
            return ""  # generated in validate()
        path = camera_service.validate_rtmp_path(value)
        if not path:
            raise serializers.ValidationError(
                "Use letters, digits, '_' or '-', optionally separated by '/', e.g. rtmp_push/D001."
            )
        return path

    def validate(self, attrs):
        # RTMP path: generated from model + serial on create, or when sent blank on edit.
        # An existing path is never changed automatically (it is configured on the camera).
        if self.instance is None or "rtmp_path" in attrs:
            if not attrs.get("rtmp_path"):
                model = attrs.get("model_number", getattr(self.instance, "model_number", ""))
                serial = attrs.get("serial_number", getattr(self.instance, "serial_number", ""))
                generated = camera_service.generate_rtmp_path(model, serial)
                if not generated:
                    raise serializers.ValidationError({"rtmp_path": "Enter an RTMP path, or a serial/model number to generate one."})
                attrs["rtmp_path"] = generated
            clash = Camera.objects.filter(rtmp_path=attrs["rtmp_path"])
            if self.instance is not None:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError({"rtmp_path": f"RTMP path '{attrs['rtmp_path']}' is already used by another camera."})

        # WebRTC URL defaults to <public base>/<rtmp_path>/. On edit, a URL that was
        # still the old default follows a path change; a custom URL is kept.
        path = attrs.get("rtmp_path") or getattr(self.instance, "rtmp_path", None)
        given = (attrs.get("webrtc_url") or "").strip()
        if given:
            attrs["webrtc_url"] = given
        elif self.instance is None or "webrtc_url" in attrs:
            attrs["webrtc_url"] = camera_service.default_webrtc_url(path)
        elif "rtmp_path" in attrs and self.instance.webrtc_url == camera_service.default_webrtc_url(self.instance.rtmp_path):
            attrs["webrtc_url"] = camera_service.default_webrtc_url(path)
        return attrs

    def create(self, validated_data):
        user = self.context.get("user")
        now = timezone.now()
        validated_data.update(created_at=now, updated_at=now, created_by=getattr(user, "id", None), updated_by=getattr(user, "id", None))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context.get("user")
        validated_data.update(updated_at=timezone.now(), updated_by=getattr(user, "id", None))
        return super().update(instance, validated_data)


class CameraEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraEvent
        fields = ["id", "camera", "event", "details", "user_id", "created_at"]


class CameraStreamSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraStreamSession
        fields = [
            "id", "camera", "reason", "user_id", "request", "order_request", "dispenser_unit",
            "transaction_id", "started_at", "expires_at", "last_heartbeat_at", "ended_at", "end_reason",
        ]


class RequestCameraSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestCameraSnapshot
        fields = [
            "id", "request", "order_request", "transaction_id", "dispenser_unit", "camera", "session",
            "dispenser_serialnumber", "dispenser_imeinumber", "dispenser_gun_mapping_id",
            "request_status", "dispense_status_code", "dispensed_volume", "dispensed_amount", "gps_coordinates",
            "kind", "image_path", "width", "height", "size_bytes", "captured_at", "created_at",
        ]


class CameraAssignmentBlockSerializer(serializers.Serializer):
    """Optional `camera` block accepted by the assignment add/edit APIs."""
    available = serializers.BooleanField()
    serial_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    model_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    brand = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    rtmp_path = serializers.CharField(max_length=150, required=False, allow_blank=True)
    webrtc_url = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs.get("available"):
            missing = [f for f in ("serial_number", "model_number") if not (attrs.get(f) or "").strip()]
            if missing:
                raise serializers.ValidationError({f: "This field is required when a camera is available." for f in missing})
            if (attrs.get("rtmp_path") or "").strip():  # blank → generated from model + serial
                path = camera_service.validate_rtmp_path(attrs["rtmp_path"])
                if not path:
                    raise serializers.ValidationError({"rtmp_path": "Use letters, digits, '_' or '-', optionally separated by '/'."})
                attrs["rtmp_path"] = path
        return attrs


# --- `camera` block on the assignment add/edit APIs -----------------------------
# The assign form manages the dispenser's primary camera (lowest id). Extra
# cameras are managed from the camera page.

CAMERA_BLOCK_FIELDS = ("serial_number", "model_number", "brand", "rtmp_path", "webrtc_url")


def validate_camera_block(raw):
    """Validate the optional `camera` block. Returns validated data, or None if absent.
    Raises serializers.ValidationError({"camera": ...}) on bad input."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, str):  # multipart/form-data sends nested objects as JSON text
        import json
        try:
            raw = json.loads(raw)
        except ValueError:
            raise serializers.ValidationError({"camera": "Must be a JSON object."})
    block = CameraAssignmentBlockSerializer(data=raw)
    if not block.is_valid():
        raise serializers.ValidationError({"camera": block.errors})
    return block.validated_data


def camera_summary(dispenser_unit_id):
    cam = Camera.objects.filter(dispenser_unit_id=dispenser_unit_id).order_by("id").first()
    if cam is None:
        return None
    return {
        "id": cam.id,
        "serial_number": cam.serial_number,
        "model_number": cam.model_number,
        "brand": cam.brand,
        "rtmp_path": cam.rtmp_path,
        "rtmp_publish_url": camera_service.rtmp_publish_url(cam),
        "webrtc_url": cam.webrtc_url,
        "stream_mode": cam.stream_mode,
        "is_active": cam.is_active,
        "camera_count": Camera.objects.filter(dispenser_unit_id=dispenser_unit_id).count(),
    }


def apply_camera_block(dispenser_unit_id, block, user):
    """Create/update/delete the dispenser's primary camera inside the caller's
    transaction. Returns a callable to run after commit (MediaMTX + event log)."""
    user_id = getattr(user, "id", None)
    existing = list(Camera.objects.filter(dispenser_unit_id=dispenser_unit_id).order_by("id"))

    if block["available"]:
        primary = existing[0] if existing else None
        data = {k: block[k] for k in CAMERA_BLOCK_FIELDS if k in block}
        data["dispenser_unit"] = dispenser_unit_id
        ser = CameraSerializer(primary, data=data, partial=primary is not None, context={"user": user})
        if not ser.is_valid():
            raise serializers.ValidationError({"camera": ser.errors})
        old_path = primary.rtmp_path if primary else None
        cam = ser.save()

        def after():
            camera_service.log_event(cam, "camera_updated" if primary else "camera_created",
                                     {"source": "assignment", "old_rtmp_path": old_path, "rtmp_path": cam.rtmp_path}, user_id)
            camera_service.on_camera_saved(cam, old_rtmp_path=old_path, user_id=user_id)
        return after

    # available = False → remove the dispenser's cameras (the form confirms first)
    removed = []
    for cam in existing:
        camera_service.end_all_sessions(cam, "camera_deleted", user_id=user_id)
        removed.append({"camera_id": cam.id, "serial_number": cam.serial_number, "rtmp_path": cam.rtmp_path})
        cam.delete()

    def after():
        from . import mediamtx
        for r in removed:
            camera_service.log_event(None, "camera_deleted", dict(r, source="assignment"), user_id)
            try:
                mediamtx.delete_path(r["rtmp_path"])
            except mediamtx.MediaMTXError as e:
                camera_service.log_event(None, "mediamtx_error", {"path": r["rtmp_path"], "action": "disable", "error": str(e)}, user_id)
    return after
