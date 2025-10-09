from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
import os
import django
from asgiref.sync import sync_to_async
from datetime import datetime
from pytz import timezone 
import base64, time
from .models import *
from existing_tables.models import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atd.settings')
django.setup()


# --- GLOBAL CONNECTION TRACKER ---
connected_clients = {}



# ---------- Token Verification Helpers ----------
def xor_with_key(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

def digit_sum(imei: str) -> int:
    return sum(int(ch) for ch in imei)

def checksum_twos(imei: str) -> int:
    s = digit_sum(imei) & 0xFF
    return (-s) & 0xFF

def verify_token(token: str, key: str):
    try:
        decrypted = xor_with_key(base64.b64decode(token), key).decode()
        imei, chk, ts = decrypted.split("|")
        expected_chk = checksum_twos(imei)
        return expected_chk == int(chk), {"imei": imei, "checksum": chk, "timestamp": int(ts)}
    except Exception:
        return False, {}

# ---------- WebSocket Consumer ----------
class DispenserControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf8')
        query_params = parse_qs(query_string)

        self.imei_number = query_params.get('imei_number', [None])[0]
        self.token = query_params.get('token', [None])[0]
        self.client_type = query_params.get('client_type', ['unknown'])[0]
        self.room_id = f"room_{self.imei_number}"
        self.channel = self.channel_name

        print(f"[CONNECT] IMEI={self.imei_number}, Token={self.token}, Type={self.client_type}")

        # Reject if client_type is not hardware or web
        if self.client_type not in ['hardware', 'web']:
            print(f"[REJECT] Invalid client_type: {self.client_type}")
            await self.close(code=4002)
            return

        # Token verification
        is_valid = await self.verify_token_and_match_imei(self.token, self.imei_number)
        if not is_valid:
            print(f"[REJECT] Token Invalid or IMEI mismatch")
            await self.close(code=4001)
            return

        # Common check: IMEI exists and assigned
        imei_ok = await self.is_imei_assigned(self.imei_number)
        if not imei_ok:
            print(f"[REJECT] IMEI not assigned or doesn't exist")
            await self.close(code=4003)
            return

        # Join room and accept connection
        await self.channel_layer.group_add(self.room_id, self.channel_name)
        await self.accept()
        await self.add_connected_client()

        # If hardware client → update connectivity status
        if self.client_type == 'hardware':
            await self.update_connectivity(self.imei_number, "online")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_id, self.channel_name)
        await self.remove_connected_client()

        # Only update status if hardware disconnects
        if self.client_type == 'hardware':
            await self.update_connectivity(self.imei_number, "offline")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Forwards the payload to all connected clients in the same room except sender.
        """
        if text_data is not None:
            await self.channel_layer.group_send(
                self.room_id,
                {
                    "type": "dispenser.text",
                    "text": text_data,
                    "sender_channel_name": self.channel_name,
                },
            )
        elif bytes_data is not None:
            await self.channel_layer.group_send(
                self.room_id,
                {
                    "type": "dispenser.bytes",
                    "bytes": bytes_data,
                    "sender_channel_name": self.channel_name,
                },
            )


    async def dispenser_text(self, event):
        if event["sender_channel_name"] != self.channel_name:
            await self.send(text_data=event["text"])

    async def dispenser_bytes(self, event):
        if event["sender_channel_name"] != self.channel_name:
            await self.send(bytes_data=event["bytes"])


    async def add_connected_client(self):
        imei = self.imei_number
        client_type = self.client_type
        connected_clients.setdefault(imei, {}).setdefault(client_type, [])
        if self.channel_name not in connected_clients[imei][client_type]:
            connected_clients[imei][client_type].append(self.channel_name)

    async def remove_connected_client(self):
        imei = self.imei_number
        client_type = self.client_type
        if imei in connected_clients and client_type in connected_clients[imei]:
            try:
                connected_clients[imei][client_type].remove(self.channel_name)
            except ValueError:
                pass

    async def send_error_message(self, error_message):
        await self.send(text_data=json.dumps({"error": error_message}))

    async def send_data(self, data):
        await self.send(text_data=json.dumps(data))

    @sync_to_async
    def verify_token_and_match_imei(self, token: str, given_imei: str) -> bool:
        key = "atd_shared_secret_key"
        valid, data = verify_token(token, key)
        print("[TOKEN VERIFY] Decoded:", data)
        return valid and data.get("imei") == given_imei

    @database_sync_to_async
    def is_imei_assigned(self, imei: str) -> bool:
        """
        Check if dispenser exists and is assigned
        """
        try:
            dispenser = DispenserUnits.objects.get(imei_number=imei)
            return dispenser.assigned_status is True
        except DispenserUnits.DoesNotExist:
            return False

    @database_sync_to_async
    def update_connectivity(self, imei: str, status: str):
        """
        Update DispenserUnits and related gun mapping connectivity_status.
        Only for hardware client.
        """
        dispenser = DispenserUnits.objects.get(imei_number=imei)
        dispenser.connectivity_status = status
        dispenser.save(update_fields=["connectivity_status"])

        Dispenser_Gun_Mapping_To_Customer.objects.filter(
            dispenser_unit_id=dispenser.id
        ).update(connectivity_status=(status == "online"))

        print(f"[STATUS] IMEI {imei} updated to {status}")


