from flask.wrappers import Request
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from flask import abort

def check_security_headers(request: Request):

    # Ensure security headers
    # Your public key can be found on your application in the Developer Portal
    PUBLIC_KEY = '5a4d255fbb9ac0df010b6844e0e9cb22b0a4a560e0d424724c7667c6a47bc01c'

    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(),
                          bytes.fromhex(signature))
    except BadSignatureError:
        abort(401, 'invalid request signature')