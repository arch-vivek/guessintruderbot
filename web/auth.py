import hashlib, hmac, time
from config import BOT_TOKEN

def verify_telegram_auth(auth_data: dict) -> bool:

    if not auth_data or "hash" not in auth_data:
        return False

    received_hash = auth_data.pop("hash")
    # Check if the data is recent (within 1 day)
    auth_date = int(auth_data.get("auth_date", 0))
    if abs(time.time() - auth_date) > 86400:
        return False

    # Build data check string
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(auth_data.items()) if v is not None
    )
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return calculated_hash == received_hash