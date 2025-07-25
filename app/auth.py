from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from .models import User
from .storage import load_users, save_users
from .utils import hash_password, verify_password

SECRET_KEY = "super-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10800

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        users = load_users()
        user = next((u for u in users if u["username"] == username), None)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")


@router.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    if any(u["username"] == form.username for u in users):
        raise HTTPException(status_code=400, detail="Username exists")
    
    # 使用 User 模型创建新用户，自动生成 UUID
    new_user = User(
        username=form.username,
        password_hash=hash_password(form.password),
        role="user"
    )
    
    users.append(new_user.dict())
    save_users(users)
    return {"msg": "Registered", "user_id": new_user.id}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    user = next((u for u in users if u["username"] == form.username), None)
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user["username"]}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}