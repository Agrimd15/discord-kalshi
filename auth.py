
import time
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

def sign_request(method, path, key_id, private_key_path):
    """
    Generates the required headers for Kalshi API v2 authentication.
    
    Args:
        method (str): HTTP method (e.g., "GET").
        path (str): API path (e.g., "/trade-api/v2/portfolio/balance").
        key_id (str): The Key ID (UUID).
        private_key_path (str): Path to the private key .pem file.
        
    Returns:
        dict: A dictionary containing the required headers:
            - KALSHI-ACCESS-KEY
            - KALSHI-ACCESS-SIGNATURE
            - KALSHI-ACCESS-TIMESTAMP
    """
    # 1. Get current timestamp in milliseconds
    timestamp = str(int(time.time() * 1000))

    # 2. Construct the message to be signed
    # Format: {timestamp}{method}{path}
    payload = f"{timestamp}{method}{path}"
    
    # 3. Load the private key
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )

    # 4. Sign the payload using RSA-PSS with SHA256
    signature = private_key.sign(
        payload.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # 5. Encode the signature in Base64
    signature_b64 = base64.b64encode(signature).decode('utf-8')

    # 6. Return the headers
    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": signature_b64,
        "KALSHI-ACCESS-TIMESTAMP": timestamp
    }
