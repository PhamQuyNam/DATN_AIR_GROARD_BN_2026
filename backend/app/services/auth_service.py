"""
app/services/auth_service.py
Xử lý: mã hóa mật khẩu, tạo/xác thực JWT token, seed tài khoản Admin mặc định.
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlmodel import Session, select
from app.models.db_models import User

# ── Cấu hình bảo mật ──────────────────────────────────────────────────────────
SECRET_KEY = "airguard-bn-secret-key-2026-datn-very-secure"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 giờ

# Dùng sha256_crypt thay bcrypt để tránh lỗi passlib 72-byte trong Python 3.9 container
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# ── Mật khẩu ──────────────────────────────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# ── Tra cứu user ──────────────────────────────────────────────────────────────
def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()

def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(session, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# ── Seed Admin mặc định ───────────────────────────────────────────────────────
def seed_default_admin(session: Session):
    """
    Tạo tài khoản Admin mặc định nếu chưa có.
    Thông tin đăng nhập: admin@airguard.vn / Admin@2026
    """
    existing = get_user_by_email(session, "admin@airguard.vn")
    if not existing:
        admin = User(
            full_name="Quản trị viên AirGuard",
            email="admin@airguard.vn",
            hashed_password=hash_password("Admin@2026"),
            role="MANAGER",
            is_active=True
        )
        session.add(admin)
        session.commit()
        print("✅ Auth: Đã tạo tài khoản Admin mặc định → admin@airguard.vn / Admin@2026")
    else:
        print("✅ Auth: Tài khoản Admin đã tồn tại.")
