import hashlib

def hash_file(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()
