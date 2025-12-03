from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# SQLite 파일 DB 경로 (프로젝트 루트에 backend.db 생성)
DATABASE_URL = "sqlite:///./backend.db"


# 엔진
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 전용 옵션
)


# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base 클래스
class Base(DeclarativeBase):
    pass


# FastAPI에서 쓰는 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
