from django.urls import path

from .camera_views import *

urlpatterns = [
    # Camera management (IOT Admin)
    path("camera/add/", AddCamera.as_view(), name="add-camera"),
    path("camera/get/", GetCameras.as_view(), name="get-cameras"),
    path("camera/get/<int:id>/", GetCameraByID.as_view(), name="get-camera-by-id"),
    path("camera/get-by-dispenser/<int:dispenser_unit_id>/", GetCamerasByDispenser.as_view(), name="get-cameras-by-dispenser"),
    path("camera/edit/<int:id>/", EditCamera.as_view(), name="edit-camera"),
    path("camera/delete/<int:id>/", DeleteCamera.as_view(), name="delete-camera"),

    # Control & monitoring
    path("camera/status/<int:id>/", CameraStatus.as_view(), name="camera-status"),
    path("camera/enable/<int:id>/", EnableCamera.as_view(), name="enable-camera"),
    path("camera/disable/<int:id>/", DisableCamera.as_view(), name="disable-camera"),
    path("camera/logs/<int:id>/", CameraLogs.as_view(), name="camera-logs"),
    path("camera/sessions/<int:id>/", CameraSessions.as_view(), name="camera-sessions"),
    path("camera/rtmp-devices/", RTMPDevices.as_view(), name="camera-rtmp-devices"),
    path("camera/mediamtx/health/", MediaMTXHealth.as_view(), name="camera-mediamtx-health"),

    # Live view
    path("camera/live/start/<int:camera_id>/", LiveStart.as_view(), name="camera-live-start"),
    path("camera/live/heartbeat/<int:session_id>/", LiveHeartbeat.as_view(), name="camera-live-heartbeat"),
    path("camera/live/stop/<int:session_id>/", LiveStop.as_view(), name="camera-live-stop"),

    # Request snapshots
    path("request-fuel-dispensing/snapshots/<int:request_id>/", GetRequestSnapshots.as_view(), name="get-request-snapshots"),
    path("request-fuel-dispensing/snapshots/<int:request_id>/latest/", GetLatestRequestSnapshot.as_view(), name="get-latest-request-snapshot"),
]
