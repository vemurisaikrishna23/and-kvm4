from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
import os
import django
from django.db.models import Q   # ✅ added

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atd.settings')
django.setup()

from asgiref.sync import sync_to_async
from datetime import datetime
from pytz import timezone 
import base64, time
from .models import *
from existing_tables.models import *
from django.utils import timezone as dj_timezone
from datetime import datetime




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
            print("hardware client connected")
            await self.update_connectivity(self.imei_number, "online")
        if self.client_type == 'web':
            print("web client connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_id, self.channel_name)
        await self.remove_connected_client()

        # Only update status if hardware disconnects
        if self.client_type == 'hardware':
            print("hardware client disconnected")
            await self.update_connectivity(self.imei_number, "offline")
        if self.client_type == 'web':
            print("web client disconnected")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receives JSON payload from sender, validates structure, performs logic,
        and then forwards to all other clients in the room (excluding sender).
        """
        if text_data is not None:
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send_error_message("Invalid JSON format")
                return

            # Mandatory fields check
            if "type" not in data or "machine" not in data:
                await self.send_error_message("Payload must include 'type' and 'machine'")
                return

            machine = data["machine"]
            msg_type = data["type"]

            if machine not in ["hardware", "web"]:
                await self.send_error_message("Invalid machine type. Allowed: 'hardware', 'web'")
                return

            if machine == "hardware":
                if msg_type == 4:
                    imei = data.get("imei")
                    status = data.get("mstatus")

                    if imei is None or status is None:
                        await self.send_error_message("IMEI and status are required")
                        return
                    
                    try:
                        int_status = int(status)
                    except ValueError:
                        await self.send_error_message("Status must be an integer-compatible value")
                        return
                    print(f"[HARDWARE MESSAGE] Received from IMEI {imei}: {status}")
                    await self.update_machine_status(imei, status)
                
                elif msg_type == 51:
                    imei = data.get("imei")
                    price_status = data.get("price_update_status")
                    volume = data.get("volume")
                    money = data.get("money")
                    ppu_level1 = data.get("ppu_level1")

                    if None in [imei, price_status, volume, money, ppu_level1]:
                        await self.send_error_message("Missing fields for type 51")
                        return
                    
                    if price_status == "success":
                        try:
                            volume_val = float(volume) / 100
                            money_val = float(money)
                            price_val = float(ppu_level1)
                        except ValueError:
                            await self.send_error_message("Invalid number format in volume, money, or ppu_level1")
                            return

                        print(f"[PRICE UPDATE] IMEI={imei}, Vol={volume_val}, ₹={money_val}, PPU={price_val}")
                        await self.update_price_fields(imei, volume_val, money_val, price_val)
                    else:
                        print(f"[SKIP PRICE UPDATE] Status = {price_status}")
                elif msg_type == 31:
                    required_fields = [
                        "imei", "time_utc", "lat", "lon", "alt_m", 
                        "sats_used", "speed_kmh", "course_deg", "has_fix",
                        "gvr_volume", "gvr_money", "gvr_ppu_level1", "gvr_ppu_level2"
                    ]

                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        await self.send_error_message(f"Missing required fields: {', '.join(missing_fields)}")
                        return

                    try:
                        imei = data["imei"]
                        print(data["lat"], data["lon"], data["alt_m"])
                        if data["lat"] == None:
                            data["lat"] = 0.0
                        if data["lon"] == None:
                            data["lon"] = 0.0
                        if data["alt_m"] == None:
                            data["alt_m"] = 0.0

                        gps_data = {
                            "time_utc": str(data["time_utc"]),
                            "lat": float(data["lat"]),
                            "lon": float(data["lon"]),
                            "alt_m": float(data["alt_m"]),
                            "sats_used": int(data["sats_used"]),
                            "speed_kmh": float(data["speed_kmh"]),
                            "course_deg": float(data["course_deg"]),
                        }
                        has_fix = bool(data["has_fix"])
                        gvr_volume = int(data["gvr_volume"])
                        gvr_money = int(data["gvr_money"])
                        gvr_ppu_level1 = int(data["gvr_ppu_level1"])

                    except (ValueError, TypeError, KeyError) as e:
                        await self.send_error_message(f"Field type conversion error: {e}")
                        return

                    print(f"[GPS + LIVE] IMEI={imei}, FIX={has_fix}, VOL={gvr_volume}, ₹={gvr_money}, PPU={gvr_ppu_level1}")

                    await self.update_gps_coordinates(imei, gps_data, has_fix)
                    await self.update_price_fields(
                        imei=imei,
                        totalizer_reading=gvr_volume / 100.0,
                        amount=gvr_money,
                        live_price=gvr_ppu_level1
                    )
                elif msg_type == 41:
                    # Validate required fields
                    required_fields = [
                        "imei", "grade", "volume", "money", "ppu",
                        "status", "mstatus", "epoch", "fuel_time", "transaction_id","gvr_money","gvr_volume"
                    ]
                    missing_fields = [f for f in required_fields if f not in data]
                    if missing_fields:
                        await self.send_error_message(f"Missing required fields: {', '.join(missing_fields)}")
                        return

                    try:
                        imei = str(data["imei"])
                        volume = float(data["volume"]) / 1000.0  # convert to liters
                        money = float(data["money"]) / 1000.0    # convert to INR
                        ppu = float(data["ppu"])
                        status = int(data["status"])
                        fuel_time = int(data["fuel_time"])
                        gvr_volume = int(data["gvr_volume"])
                        gvr_money = int(data["gvr_money"])
                        epoch = int(data["epoch"])
                        dispense_time = dj_timezone.make_aware(
                            datetime.fromtimestamp(epoch),
                            dj_timezone.get_current_timezone()
                        )
                        transaction_id = str(data["transaction_id"])
                    except (ValueError, TypeError, KeyError) as e:
                        await self.send_error_message(f"Field type conversion error: {e}")
                        return
                
                    print(f"[DISPENSE FINAL] TXN={transaction_id} IMEI={imei} VOL={volume} ₹={money}")

                    # Update DB without status
                    dispense_transaction_result = await self.update_dispense_transaction_details(
                        transaction_id=transaction_id,
                        imei=imei,
                        ppu=ppu,
                        volume=volume,
                        money=money,
                        dispense_time=dispense_time,
                        fuel_time=fuel_time,
                        gvr_money=gvr_money,
                        gvr_volume=gvr_volume
                    )

                    # Set status separately
                    request_status_result = await self.update_request_status_from_status_code(transaction_id,imei, status)
                    if "error" in dispense_transaction_result:
                        await self.send_error_message(dispense_transaction_result["error"])
                        return
                    else:
                        print(f"[DISPENSE TRANSACTION UPDATED] TXN={transaction_id} → Status={dispense_transaction_result['request_status']} from code={status}")
                    if "error" in request_status_result:
                        await self.send_error_message(request_status_result["error"])
                        return
                    else:
                        if str(transaction_id).upper().startswith("VIN"):
                            self.send_data({"type":99,"machine": "hardware","data":transaction_id})
                            vin_update = await self.mark_vin_vehicle_status_true(transaction_id)
                            self.send_data({"type":99,"machine": "hardware","data":vin_update})
                            if "error" in vin_update:
                                await self.send_error_message(vin_update["error"])
                                print(f"[VIN FLAG][WARN] TXN={transaction_id} could not update VIN_Vehicle.status=True → {vin_update['error']}")
                                return
                            else:
                                self.send_data({"type":99,"machine": "hardware","set to true":transaction_id})
                                print(f"[VIN FLAG] TXN={transaction_id} VIN_Vehicle.status set to True")

                        print(f"[REQUEST STATUS UPDATED] TXN={transaction_id} → Status={request_status_result['request_status']} from code={status}")
                elif msg_type == 11:
                    required_fields = [
                        "imei", "transaction_id", "preset_state", "preset_volume_req", "preset_amount_req",
                        "rfid_valid", "vehicle_tag_id", "live_preset_volume", "live_preset_price",
                        "fuel_state", "status"
                    ]

                    if data.get("status") == 200:
                        required_fields += ["gvr_amount", "gvr_volume","time_utc", "lat", "lon", "alt_m", "sats_used", "speed_kmh", "course_deg"]
                    missing_fields = [f for f in required_fields if f not in data]
                    if missing_fields:
                        await self.send_error_message(f"Missing required fields: {', '.join(missing_fields)}")
                        return

                    try:
                        imei = str(data["imei"])
                        transaction_id = str(data["transaction_id"])
                        preset_state = int(data["preset_state"])
                        preset_volume_req = float(data["preset_volume_req"])
                        preset_amount_req = float(data["preset_amount_req"])
                        rfid_valid = bool(data["rfid_valid"])
                        vehicle_tag_id = str(data["vehicle_tag_id"])
                        live_preset_volume = float(data["live_preset_volume"])
                        live_preset_price = float(data["live_preset_price"])
                        fuel_state = bool(data["fuel_state"])
                        status = int(data["status"])
                    except (ValueError, TypeError, KeyError) as e:
                        await self.send_error_message(f"Field type conversion error: {e}")
                        return


                    # Handle GPS + Totalizer if status == 200
                    if status == 200:
                        try:
                            totalizer_volume_starting = float(data["gvr_volume"]/100)
                            totalizer_price_starting = float(data["gvr_amount"])

                            # GPS fallbacks
                            lat = 0.0 if data["lat"] is None else float(data["lat"])
                            lon = 0.0 if data["lon"] is None else float(data["lon"])
                            alt_m = 0.0 if data["alt_m"] is None else float(data["alt_m"])

                            gps_coordinates_starting = {
                                "time_utc": str(data["time_utc"]),
                                "lat": lat,
                                "lon": lon,
                                "alt_m": alt_m,
                                "sats_used": int(data["sats_used"]),
                                "speed_kmh": float(data["speed_kmh"]),
                                "course_deg": float(data["course_deg"]),
                            }

                            # Optional: Save totalizer and GPS data to DB here or pass to function
                            await self.save_totalizer_and_gps_starting(transaction_id, imei, totalizer_volume_starting, totalizer_price_starting, gps_coordinates_starting)

                        except (ValueError, TypeError, KeyError) as e:
                            await self.send_error_message(f"GPS/Totalizer parsing error: {e}")
                            return
                    # Forward to DB update
                    result = await self.update_transaction_log(data)
                    request_status_result = await self.update_request_status_from_status_code(transaction_id, imei, status)
                    if "error" in request_status_result:
                        print(f"[ERROR] Request status update failed: {request_status_result['error']}")
                        await self.send_error_message(request_status_result["error"])
                        return
                    else:
                        print(f"[REQUEST STATUS UPDATED] TXN={transaction_id} → Status={request_status_result['request_status']} from code={status}")

                    if "error" in result:
                        print(f"[ERROR] Preset log update failed: {result['error']}")
                        await self.send_error_message(result["error"])
                        return
                    else:
                        print(f"[PRESET LOG] Updated for TXN={transaction_id} IMEI={imei}")

                else:
                    pass

            # Forward to group (excluding sender)
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


    @database_sync_to_async
    def update_machine_status(self, imei: str, status: str):
        """
        Update the machine_status field in Dispenser_Gun_Mapping_To_Customer
        for the dispenser unit with the given IMEI.
        """
        try:
            dispenser = DispenserUnits.objects.get(imei_number=imei)
            affected = Dispenser_Gun_Mapping_To_Customer.objects.filter(
                dispenser_unit_id=dispenser.id
            ).update(machine_status=status)

            print(f"[MACHINE STATUS] Updated {affected} mapping(s) for IMEI {imei} to status {status}")

        except DispenserUnits.DoesNotExist:
            print(f"[ERROR] IMEI {imei} not found in DispenserUnits for machine status update")

    @database_sync_to_async
    def update_price_fields(self, imei, totalizer_reading, amount, live_price):
        try:
            dispenser = DispenserUnits.objects.get(imei_number=imei)
            Dispenser_Gun_Mapping_To_Customer.objects.filter(
                dispenser_unit_id=dispenser.id
            ).update(
                live_totalizer_reading=totalizer_reading,
                live_total_reading_amount=amount,
                live_price=live_price
            )
            print(f"[UPDATED LIVE DATA] IMEI={imei}")
        except DispenserUnits.DoesNotExist:
            print(f"[ERROR] IMEI {imei} not found for price update")


    @database_sync_to_async
    def save_totalizer_and_gps_starting_with_validation(self, transaction_id, imei, totalizer_vol, totalizer_price, gps_data):
        try:
            txn = RequestFuelDispensingDetails.objects.get(transaction_id=transaction_id)
        except RequestFuelDispensingDetails.DoesNotExist:
            print(f"[ERROR] TXN not found: {transaction_id}")
            return

        if txn.dispenser_imeinumber != imei:
            print(f"[IMEI MISMATCH] {imei} != {txn.dispenser_imeinumber}")
            return

        # 1. Get dispenser_gun_mapping_id of this txn
        dispenser_gun_mapping_id = txn.dispenser_gun_mapping_id

        # 2. Find the last transaction of this dispenser_gun_mapping_id
        last_txn = (
            RequestFuelDispensingDetails.objects
            .filter(dispenser_gun_mapping_id=dispenser_gun_mapping_id)
            .exclude(id=txn.id)  # exclude current one
            .order_by("-request_created_at")  # last one
            .first()
        )

        # 3. Perform validation
        totalizer_validation = None
        if last_txn:
            if last_txn.totalizer_price_ending == totalizer_price:
                totalizer_validation = 0
            else:
                totalizer_validation = 1

        # 4. Save into current txn
        txn.totalizer_volume_starting = totalizer_vol
        txn.totalizer_price_starting = totalizer_price
        txn.gps_coordinates_starting = gps_data
        if totalizer_validation is not None:
            txn.totalizer_validation = totalizer_validation

        txn.save(update_fields=[
            "totalizer_volume_starting",
            "totalizer_price_starting",
            "gps_coordinates_starting",
            "totalizer_validation"
        ])
        print(f"[START DATA SAVED] TXN={transaction_id}, Validation={totalizer_validation}")



    @database_sync_to_async
    def update_gps_coordinates(self, imei, gps_data: dict, has_fix: bool):
        try:
            dispenser = DispenserUnits.objects.get(imei_number=imei)
            dispenser_mapping = Dispenser_Gun_Mapping_To_Customer.objects.get(dispenser_unit=dispenser)
            current_gps = dispenser_mapping.gps_coordinates or {}

            if has_fix:
                # Valid GPS fix → update all with live_data=True
                gps_data["live_data"] = True
                dispenser_mapping.gps_coordinates = gps_data
            else:
                # No fix: retain previous, update live_data to False
                if current_gps:
                    current_gps["live_data"] = False
                    dispenser_mapping.gps_coordinates = current_gps
                else:
                    gps_data["live_data"] = False
                    dispenser_mapping.gps_coordinates = gps_data

            dispenser_mapping.save(update_fields=["gps_coordinates"])
            print(f"[GPS UPDATED] IMEI={imei}, live_data={dispenser_mapping.gps_coordinates['live_data']}")

        except DispenserUnits.DoesNotExist:
            print(f"[ERROR] Dispenser with IMEI {imei} not found for GPS update")



    @database_sync_to_async
    def update_dispense_transaction_details(self, transaction_id, imei, ppu, volume, money, dispense_time, fuel_time,gvr_money,gvr_volume):
        try:
            txn = RequestFuelDispensingDetails.objects.get(transaction_id=transaction_id)
        except RequestFuelDispensingDetails.DoesNotExist:
            return {"error": "Transaction ID not found"}

        if txn.dispenser_imeinumber != imei:
            return {"error": "IMEI mismatch with transaction record."}


        txn.dispenser_live_price = ppu
        txn.dispenser_received_volume = volume
        txn.dispenser_received_price = money
        txn.dispense_end_time = dispense_time
        txn.dispense_time_taken = fuel_time
        txn.totalizer_volume_ending = gvr_volume / 100
        txn.totalizer_price_ending = gvr_money
        txn.save(update_fields=[
            "dispenser_live_price",
            "dispenser_received_volume",
            "dispenser_received_price",
            "dispense_end_time",
            "dispense_time_taken",
            "totalizer_volume_ending",
            "totalizer_price_ending"
        ])
        print(f"[TXN UPDATED] Transaction {transaction_id} updated successfully")
        return {"success": True,"request_status": txn.request_status}



    @database_sync_to_async
    def update_transaction_log(self, data):

        transaction_id = data.get("transaction_id")
        imei = data.get("imei")

        try:
            request = RequestFuelDispensingDetails.objects.get(transaction_id=transaction_id)
            if request.dispenser_imeinumber != imei:
                return {"error": "IMEI mismatch with transaction record."}

            # Prepare log (exclude these fields)
            log_data = {
                k: v for k, v in data.items()
                if k not in ["type", "machine", "transaction_id", "imei"]
            }

            # Append to or initialize log
            if isinstance(request.transaction_log, list):
                request.transaction_log.append(log_data)
            elif request.transaction_log:
                request.transaction_log = [request.transaction_log, log_data]
            else:
                request.transaction_log = [log_data]

            request.save(update_fields=["transaction_log"])
            return {"success": True}

        except RequestFuelDispensingDetails.DoesNotExist:
            return {"error": "Transaction ID not found"}

    @database_sync_to_async
    def update_request_status_from_status_code(self, transaction_id: str, imei: str, status_code: int):
        try:
            txn = RequestFuelDispensingDetails.objects.get(transaction_id=transaction_id)
            if txn.dispenser_imeinumber != imei:
                print(f"[SKIP STATUS] IMEI mismatch for TXN={transaction_id}")
                return

            # Map status_code to request_status

            if status_code == 200:
                request_status = 1  # Hardware Received
            elif status_code == 0:
                request_status = 0  # Pending
            elif status_code in [201,202, 206]:
                request_status = 2  # Dispensing
            elif status_code in [203,204]:
                request_status = 3  # Completed
            elif status_code == 205:
                request_status = 4  # Interrupted
            elif status_code in [400, 401,402, 410, 411, 420]:
                request_status = 5  # Failed

            else:
                request_status = 5  #Failed

            txn.request_status = request_status
            txn.dispense_status_code = status_code
            txn.save(update_fields=["request_status", "dispense_status_code"])
            print(f"[REQUEST STATUS UPDATED] TXN={transaction_id} → Status={request_status} from code={status_code}")
            return {"success": True,"request_status": request_status}

        except RequestFuelDispensingDetails.DoesNotExist:
            print(f"[ERROR] TXN={transaction_id} not found for request status update")
            return {"error": "Transaction ID not found"}

    @sync_to_async
    def mark_vin_vehicle_status_true(self,txn_id: str):
        """
        Finds the latest VIN_Vehicle row for this exact transaction_id
        and sets status=True. Returns a small result dict.
        """
        try:
            row =VIN_Vehicle.objects.get(transaction_id=txn_id)
            if not row:
                return {"error": f"VIN_Vehicle not found for transaction_id={txn_id}"}
            if getattr(row, "status", None) is not True:
                row.status = True
                row.save(update_fields=["status"])
            return {"ok": True}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}