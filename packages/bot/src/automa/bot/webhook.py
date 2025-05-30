import base64
import hashlib
import hmac
import json
from datetime import datetime


def verify_webhook(secret: str, signature: str, payload: str) -> bool:
    if (
        not secret
        or not isinstance(secret, str)
        or not signature
        or not isinstance(signature, str)
    ):
        return False

    if not secret.startswith("atma_whsec_"):
        raise ValueError("Secret must start with 'atma_whsec_'")

    signatures = signature.split(" ")
    generated_signature = generate_webhook_signature(secret, payload)

    # Use constant-time comparison to prevent timing attacks
    return any(hmac.compare_digest(generated_signature, sig) for sig in signatures)


def generate_webhook_signature(secret: str, payload: str) -> str:
    try:
        msg = json.loads(payload)
    except json.JSONDecodeError:
        raise ValueError("Invalid payload format")

    if not isinstance(msg, dict):
        raise ValueError("Invalid payload format")

    id = msg.get("id")
    timestamp = msg.get("timestamp")

    if not id or not timestamp:
        raise ValueError("Payload must contain both 'id' and 'timestamp' fields")

    # Convert timestamp from ISO to epoch time in seconds
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    timestamp = int(dt.timestamp())

    sig = base64.b64encode(
        hmac.new(
            secret[11:].encode("utf-8"),
            f"{id}.{timestamp}.{payload}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    return f"v1,{sig}"
