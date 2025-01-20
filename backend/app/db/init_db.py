# backend/app/db/init_db.py
from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.models.note import Note

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()