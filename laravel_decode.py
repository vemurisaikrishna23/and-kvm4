import pymysql
import hashlib

# Laravel database configuration
DB_CONFIG = {
    'host': 'Atd-iot-db.coh7dtk0kjb8.ap-south-1.rds.amazonaws.com',
    'user': 'iotjaideep',
    'password': 'k8P3x7M1s4',
    'database': 'atd_uat_db',
    'port': 3306
}

TOKEN = "10|M3xiL2oF4TEO2pEbGUzijGhsrKSdXmIZVvheX880c270ab90"  # Sanctum token


def get_user_id_from_sanctum_token(token: str):
    try:
        token_id, token_plaintext = token.split("|", 1)
    except ValueError:
        raise ValueError("Invalid Sanctum token format. Must be 'id|plaintext'")

    hashed_token = hashlib.sha256(token_plaintext.encode()).hexdigest()

    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT tokenable_id, tokenable_type
                FROM personal_access_tokens
                WHERE id = %s AND token = %s
            """
            cursor.execute(sql, (token_id, hashed_token))
            row = cursor.fetchone()

            if row:
                user_id, user_type = row
                return {
                    'user_id': user_id,
                    'user_type': user_type
                }
            else:
                return None
    finally:
        connection.close()

if __name__ == "__main__":
    result = get_user_id_from_sanctum_token(TOKEN)
    if result:
        print(f"✅ Token belongs to user_id: {result['user_id']} ({result['user_type']})")
    else:
        print("❌ Invalid token or user not found.")
