import hashlib
import struct
import sys
from typing import Dict, Optional, Any
from binascii import hexlify, unhexlify
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PASSWORD = "OSD"

def PBKDF1(s: str, salt: bytes, lenout: int, hashfunc: Any, iter_: int) -> bytes:
    m = hashfunc
    digest = m(s.encode("utf-8") + salt).digest()
    for i in range(iter_-1):
        digest = m(digest).digest()
    return digest[:lenout]

def generate(salt: bytes) -> bytes:
    return PBKDF1(PASSWORD, salt, 32, hashlib.sha256, 1000)

def decrypt_file(fi_path: str, fo_path: str, lang: Optional[Dict[str, str]] = None) -> bool:
    lang = lang or {}
    try:
        with open(fi_path, "rb") as fi:
            iv = fi.read(16)
            salt = fi.read(16)
            encrypted_body = fi.read()

        key = generate(salt)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        plain = decryptor.update(encrypted_body) + decryptor.finalize()

        original_size = struct.unpack('<q', plain[0:8])[0]
        signature = plain[8:16]
        if signature != b'\xcf\x06\x05\x04\x03\x02\x01\xfc':
            print(lang.get("img_decrypt_broken", "Broken file."))
            return False

        body = plain[16:16 + original_size]
        digest = hashlib.sha256(body).digest()
        if digest != plain[16 + original_size:16 + original_size + 32]:
            print(lang.get("img_decrypt_broken", "Broken file."))
            return False

        with open(fo_path, "wb") as fo:
            fo.write(body)
            
        print(lang.get("img_decrypt_success", "Successfully decrypted."), original_size, "bytes")
        return True

    except Exception as e:
        print(lang.get("img_decrypt_error", f"Error decrypting {fi_path}: {e}").format(path=fi_path, e=e), file=sys.stderr)
        return False