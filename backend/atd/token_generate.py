import base64, time

def xor_with_key(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

def digit_sum(imei: str) -> int:
    return sum(int(ch) for ch in imei)

def checksum_twos(imei: str) -> int:
    s = digit_sum(imei) & 0xFF
    return (-s) & 0xFF

def generate_token(imei: str, key: str) -> str:
    ts = int(time.time())
    print(ts)
    chk = checksum_twos(imei)
    payload = f"{imei}|{chk}|{ts}".encode()
    encrypted = xor_with_key(payload, key)
    token = base64.b64encode(encrypted).decode()
    return token

def verify_token(token: str, key: str):
    try:
        decrypted = xor_with_key(base64.b64decode(token), key).decode()
        imei, chk, ts = decrypted.split("|")
        expected_chk = checksum_twos(imei)
        return expected_chk == int(chk), {"imei": imei, "checksum": chk, "timestamp": ts}
    except Exception:
        return False, {}

# Example
key = "atd_shared_secret_key"
imei = "999999999999999"
token = generate_token(imei, key)
print("Token:", token)
valid, data = verify_token(token, key)
print("Valid:", valid, data)