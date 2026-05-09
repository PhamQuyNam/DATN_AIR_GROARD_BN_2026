"""
app/api/routes/auth.py
Các endpoints: Đăng ký, Đăng nhập, Lấy thông tin user hiện tại.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_session
from app.models.db_models import User
from app.services.auth_service import (
    authenticate_user, create_access_token, decode_token,
    get_user_by_email, hash_password
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str

# ── Dependency: Lấy user hiện tại từ token ────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ hoặc đã hết hạn")
    
    email = payload.get("sub")
    user = get_user_by_email(session, email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại")
    return user

def get_current_manager(current_user: User = Depends(get_current_user)) -> User:
    """Dependency bảo vệ route - chỉ cho phép MANAGER truy cập."""
    if current_user.role != "MANAGER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ nhà quản lý mới có quyền thực hiện thao tác này"
        )
    return current_user

# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/auth/register", status_code=201)
def register(req: RegisterRequest, session: Session = Depends(get_session)):
    """Đăng ký tài khoản Người dân (CITIZEN)."""
    existing = get_user_by_email(session, req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    
    user = User(
        full_name=req.full_name,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="CITIZEN"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "Đăng ký thành công", "email": user.email, "role": user.role}

@router.post("/auth/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Đăng nhập và nhận JWT Token. Username = email."""
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "full_name": user.full_name
    }

@router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Lấy thông tin tài khoản đang đăng nhập."""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }
