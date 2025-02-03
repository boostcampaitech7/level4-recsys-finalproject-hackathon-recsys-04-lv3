import os

import uvicorn
from app.api.endpoints import auth, note, quiz, rag, user
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title=settings.PROJECT_NAME)

# uploads 폴더의 절대 경로를 얻습니다
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 절대 경로로 정적 파일을 마운트
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(note.router, prefix=f"{settings.API_V1_STR}/note", tags=["note"])
app.include_router(rag.router, prefix=f"{settings.API_V1_STR}/rag", tags=["rag"])
app.include_router(quiz.router, prefix=f"{settings.API_V1_STR}/quiz", tags=["quiz"])
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
