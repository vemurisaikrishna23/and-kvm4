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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atd.settings')
django.setup()


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


class DispenserControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode('utf8')
        query_params = parse_qs(query_string)

        self.imei_number = query_params.get('imei_number', [None])[0]
        self.token = query_params.get('token', [None])[0]
        self.room_id = f"room_{self.imei_number}"
        print(self.imei_number, self.token)

        is_valid = await self.verify_token_and_match_imei(self.token, self.imei_number)
        print(is_valid)
        if is_valid:
            await self.channel_layer.group_add(
            self.room_id,
            self.channel_name
        )
            await self.accept()
        else:
            await self.close(code=4001)
            return

        # Add to group and accept connection

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_id,
            self.channel_name
        )

    @sync_to_async
    def verify_token_and_match_imei(self, token: str, given_imei: str) -> bool:
        key = "atd_shared_secret_key"
        valid, data = verify_token(token, key)
        print(valid, data)
        return valid and data.get("imei") == given_imei




