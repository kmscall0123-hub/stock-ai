from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    market = Column(String(32), nullable=False)
    sector = Column(String(64), nullable=True)
    currency = Column(String(8), nullable=False, default="KRW")

    # 🔹 추가: 종목 1개가 여러 가격(일자)을 가질 수 있는 관계
    prices = relationship("Price", back_populates="stock")


# 🔹 새로 추가할 가격 테이블
class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, index=True)

    stock_id = Column(Integer, ForeignKey("stocks.id"), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)

    # 관계: 가격 → 종목
    stock = relationship("Stock", back_populates="prices")