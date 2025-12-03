from typing import List, Optional
from sqlalchemy.orm import Session

from backend import models, schemas


def create_stock(db: Session, stock_in: schemas.StockCreate) -> models.Stock:
    # symbol 중복 체크
    exist = db.query(models.Stock).filter(models.Stock.symbol == stock_in.symbol).first()
    if exist:
        raise ValueError("Symbol already exists")

    db_stock = models.Stock(
        symbol=stock_in.symbol,
        name=stock_in.name,
        market=stock_in.market,
        sector=stock_in.sector,
        currency=stock_in.currency,
    )
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


def get_stock(db: Session, stock_id: int) -> Optional[models.Stock]:
    return db.query(models.Stock).filter(models.Stock.id == stock_id).first()


def list_stocks(db: Session, skip: int = 0, limit: int = 100) -> List[models.Stock]:
    return db.query(models.Stock).offset(skip).limit(limit).all()

# ✅ 여기부터 새로 추가

def update_stock(
    db: Session,
    stock_id: int,
    stock_in: schemas.StockCreate,
) -> Optional[models.Stock]:
    """기존 종목 정보를 새로운 값으로 업데이트"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        return None

    # symbol을 바꾸려 할 때, 다른 종목과 중복인지 체크
    if stock.symbol != stock_in.symbol:
        exist = db.query(models.Stock).filter(models.Stock.symbol == stock_in.symbol).first()
        if exist:
            raise ValueError("Symbol already exists")

    stock.symbol = stock_in.symbol
    stock.name = stock_in.name
    stock.market = stock_in.market
    stock.sector = stock_in.sector
    stock.currency = stock_in.currency

    db.commit()
    db.refresh(stock)
    return stock


def delete_stock(db: Session, stock_id: int) -> bool:
    """종목 삭제. 삭제 성공시 True, 없으면 False"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        return False

    db.delete(stock)
    db.commit()
    return True

# ---------- 가격 CRUD 추가 ----------

def create_price(db: Session, price_in: schemas.PriceCreate) -> models.Price:
    """하루(또는 한 시점)의 가격 데이터 한 줄 추가"""
    # 1) 해당 stock_id가 실제로 존재하는지 확인
    stock = db.query(models.Stock).filter(models.Stock.id == price_in.stock_id).first()
    if not stock:
        raise ValueError("존재하지 않는 stock_id 입니다.")

    # 2) 같은 날짜 데이터가 이미 있다면 업데이트할지, 막을지 선택
    # 여기서는 "중복이면 에러"로 막자
    exist = (
        db.query(models.Price)
        .filter(
            models.Price.stock_id == price_in.stock_id,
            models.Price.date == price_in.date,
        )
        .first()
    )
    if exist:
        raise ValueError("이미 해당 날짜의 가격 데이터가 존재합니다.")

    db_price = models.Price(
        stock_id=price_in.stock_id,
        date=price_in.date,
        open=price_in.open,
        high=price_in.high,
        low=price_in.low,
        close=price_in.close,
        volume=price_in.volume,
    )
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


def list_prices_by_stock(
    db: Session,
    stock_id: int,
    skip: int = 0,
    limit: int = 200,
) -> List[models.Price]:
    """특정 종목의 가격 데이터 여러 줄 조회 (최근 순서로)"""
    return (
        db.query(models.Price)
        .filter(models.Price.stock_id == stock_id)
        .order_by(models.Price.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_price(db: Session, price_id: int) -> Optional[models.Price]:
    """가격 데이터 한 줄 (id로) 조회"""
    return db.query(models.Price).filter(models.Price.id == price_id).first()