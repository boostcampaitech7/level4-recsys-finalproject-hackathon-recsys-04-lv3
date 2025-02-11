import uuid

from app.api import deps
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic 모델 수정
class UserCreate(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(deps.get_db)):
    # 기존 유저 체크
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="ID already registered")

    # 새로운 유저 생성
    user_id = str(uuid.uuid4())[:8]
    db_user = User(
        user_id=user_id, email=user.email, password=user.password, del_yn="N"
    )  # 실제 서비스에서는 암호화 필요
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    print(f"User id: {user_id}, Id: {user.email}, PW: {user.password}")

    return {"user_id": user_id, "message": "User created successfully"}


@router.post("/login")
def login(user: UserCreate, db: Session = Depends(deps.get_db)):
    db_user = (
        db.query(User).filter(User.email == user.email, User.del_yn == "N").first()
    )

    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Incorrect ID or password")

    return {
        "user_id": db_user.user_id,
        "id": db_user.email,
        "message": "Login successful",
    }


@router.get("/user/{user_id}")
def get_user_info(user_id, db: Session = Depends(deps.get_db)):
    user = db.query(User).filter(User.user_id == user_id, User.del_yn == "N").first()

    if not user:
        raise HTTPException(status_code=400, detail="Not Found User")

    return {
        "user_id": user.user_id,
        "email": user.email,
        "signup_date": user.created_at,
        "notes_count": 10,  # 수정 필요
        "quizzes_completed": 0,  # 수정 필요
        "feedback_received": 0,  # 수정 필요
    }
