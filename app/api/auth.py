from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.models import User
from app.schemas.schemas import Token, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    
    # If user doesn't exist, create an admin user on the fly for seamless demo
    if not user and login_data.username == "admin" and login_data.password == "admin123":
        user = User(
            username="admin",
            email="admin@vigila.cloud",
            hashed_password=get_password_hash("admin123"),
            role="ADMIN"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas (Usuario o contraseña inválidos)"
        )

    access_token = create_access_token(subject=user.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(username: str = "admin", db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

