import hashlib
import hmac
import os
import struct


def _derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return dk[:32], dk[32:]


def _keystream(key: bytes, length: int, nonce: bytes) -> bytes:
    out = b""
    counter = 0
    while len(out) < length:
        block = hashlib.sha256(key + nonce + struct.pack(">Q", counter)).digest()
        out += block
        counter += 1
    return out[:length]


def encrypt(plaintext: str, password: str) -> bytes:
    salt = os.urandom(16)
    nonce = os.urandom(16)
    enc_key, mac_key = _derive_keys(password, salt)

    pt = plaintext.encode("utf-8")
    ct = bytes(a ^ b for a, b in zip(pt, _keystream(enc_key, len(pt), nonce)))

    tag = hmac.new(mac_key, salt + nonce + ct, hashlib.sha256).digest()
    return salt + nonce + ct + tag


def decrypt(data: bytes, password: str) -> str:
    salt = data[:16]
    nonce = data[16:32]
    tag = data[-32:]
    ct = data[32:-32]

    enc_key, mac_key = _derive_keys(password, salt)

    expected = hmac.new(mac_key, salt + nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("HMAC verification failed")

    pt = bytes(a ^ b for a, b in zip(ct, _keystream(enc_key, len(ct), nonce)))
    return pt.decode("utf-8")
