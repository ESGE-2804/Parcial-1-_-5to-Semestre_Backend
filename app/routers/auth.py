import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlmodel import select
from db import SessionDep
from models import Usuario
from jose import jwt, JWTError

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-jwt-key-change-it")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

security = HTTPBearer()
router = APIRouter(tags=["Usuarios y Autenticación"])

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(session: SessionDep, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Usuario:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token no válido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
        
    user = session.get(Usuario, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(data: UserRegister, session: SessionDep):
    statement = select(Usuario).where(Usuario.email == data.email)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="El correo ya se encuentra registrado")
    
    nuevo_usuario = Usuario(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password)
    )
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return {"id": nuevo_usuario.id, "name": nuevo_usuario.name, "email": nuevo_usuario.email}

@router.post("/login")
def login(data: UserLogin, session: SessionDep):
    statement = select(Usuario).where(Usuario.email == data.email)
    user = session.exec(statement).first()
    if not user or user.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    token = create_access_token({"sub": str(user.id), "name": user.name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email}
    }

@router.get("/users/{id}")
def get_user_profile(id: int, session: SessionDep):
    user = session.get(Usuario, id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user.id, "name": user.name, "email": user.email}