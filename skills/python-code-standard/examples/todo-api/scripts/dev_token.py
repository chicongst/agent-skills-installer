"""Create a local RSA key pair (once) and print a signed development token.

uv run python scripts/dev_token.py [subject]
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

KEY_DIR = Path(".dev")
ISSUER = "https://dev.local"
AUDIENCE = "todo-api"


def _private_key() -> rsa.RSAPrivateKey:
    private_file = KEY_DIR / "jwt-private.pem"
    if private_file.exists():
        key = serialization.load_pem_private_key(private_file.read_bytes(), password=None)
        if not isinstance(key, rsa.RSAPrivateKey):
            msg = f"{private_file} is not an RSA key"
            raise TypeError(msg)
        return key
    KEY_DIR.mkdir(exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_file.write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    private_file.chmod(0o600)
    (KEY_DIR / "jwt-public.pem").write_bytes(
        key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    )
    return key


def main() -> None:
    subject = sys.argv[1] if len(sys.argv) > 1 else "dev-user"
    now = datetime.now(UTC)  # noqa: TID251
    claims = {"sub": subject, "iss": ISSUER, "aud": AUDIENCE, "iat": now, "exp": now + timedelta(hours=8)}
    print(jwt.encode(claims, _private_key(), algorithm="RS256"))


if __name__ == "__main__":
    main()
