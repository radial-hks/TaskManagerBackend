import bcrypt
import uuid
from datetime import datetime


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())


def generate_id():
    return str(uuid.uuid4())


def now_iso():
    return datetime.utcnow().isoformat()