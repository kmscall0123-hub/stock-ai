import math

from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend import models, schemas, crud
from backend.indicators import calc_sma, calc_momentum, calc_rsi




# ---- DB 테이블 생성 ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI 앱 생성 (한글 제목/설명) ----
app = FastAPI(
    title="주식 AI 보조 백엔드",
    description="뉴스·지표·간단 예측을 한 눈에 보여주는 개인용 주식 분석 시스템의 백엔드 API",
)

# ---- CORS (나중에 React 연결용) ----
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 기본 헬스체크 ----
@app.get("/", summary="서버 상태 확인", description="백엔드 서버가 정상 동작하는지 확인용 엔드포인트입니다.")
def root():
    return {"메시지": "백엔드 서버 정상 동작 중"}



# ---- 종목 API ----

@app.post(
    "/stocks",
    response_model=schemas.StockRead,
    summary="종목 등록",
    description="새로운 종목(심볼, 이름, 시장, 섹터 등)을 DB에 등록합니다.",
)
def create_stock(
    stock_in: schemas.StockCreate,
    db: Session = Depends(get_db),
):
    try:
        stock = crud.create_stock(db=db, stock_in=stock_in)
        return stock
    except ValueError as e:
        # 여기서 에러 메시지도 한글로
        raise HTTPException(status_code=400, detail=f"종목 등록 실패: {e}")


@app.get(
    "/stocks",
    response_model=List[schemas.StockRead],
    summary="종목 목록 조회",
    description="현재 DB에 저장된 종목 목록을 조회합니다.",
)
def list_stocks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    stocks = crud.list_stocks(db=db, skip=skip, limit=limit)
    return stocks


@app.get(
    "/stocks/{stock_id}",
    response_model=schemas.StockRead,
    summary="특정 종목 조회",
    description="종목 ID를 이용해 특정 종목 정보를 조회합니다.",
)
def get_stock(
    stock_id: int,
    db: Session = Depends(get_db),
):
    stock = crud.get_stock(db=db, stock_id=stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="해당 ID의 종목을 찾을 수 없습니다.")
    return stock

# ✅ 여기부터 새로 추가

@app.put(
    "/stocks/{stock_id}",
    response_model=schemas.StockRead,
    summary="종목 정보 수정",
    description="기존에 등록된 종목의 심볼/이름/시장/섹터/통화를 수정합니다.",
)
def update_stock(
    stock_id: int,
    stock_in: schemas.StockCreate,
    db: Session = Depends(get_db),
):
    stock = crud.update_stock(db=db, stock_id=stock_id, stock_in=stock_in)
    if stock is None:
        raise HTTPException(status_code=404, detail="수정하려는 종목을 찾을 수 없습니다.")
    return stock


@app.delete(
    "/stocks/{stock_id}",
    summary="종목 삭제",
    description="ID에 해당하는 종목을 DB에서 삭제합니다.",
)
def delete_stock(
    stock_id: int,
    db: Session = Depends(get_db),
):
    ok = crud.delete_stock(db=db, stock_id=stock_id)
    if not ok:
        raise HTTPException(status_code=404, detail="삭제하려는 종목을 찾을 수 없습니다.")
    # 삭제 성공했으면 간단한 메시지 반환
    return {"메시지": f"{stock_id}번 종목 삭제 완료"}

# ---------- 가격 API 시작 ----------

@app.post(
    "/prices",
    response_model=schemas.PriceRead,
    summary="가격 데이터 등록",
    description="특정 종목에 대해 일자별 시가/고가/저가/종가/거래량 데이터를 한 줄 등록합니다.",
)
def create_price(
    price_in: schemas.PriceCreate,
    db: Session = Depends(get_db),
):
    try:
        price = crud.create_price(db=db, price_in=price_in)
        return price
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"가격 등록 실패: {e}")

@app.get(
    "/prices/by_stock/{stock_id}",
    response_model=List[schemas.PriceRead],
    summary="특정 종목의 가격 목록 조회",
    description="특정 종목(stock_id)에 대한 가격 데이터를 여러 줄 조회합니다. 최신 날짜부터 정렬됩니다.",
)
def list_prices_for_stock(
    stock_id: int,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    prices = crud.list_prices_by_stock(db=db, stock_id=stock_id, skip=skip, limit=limit)
    return prices

@app.get(
    "/prices/{price_id}",
    response_model=schemas.PriceRead,
    summary="가격 데이터 단건 조회",
    description="가격 데이터 ID로 가격 한 줄을 조회합니다.",
)
def get_price(
    price_id: int,
    db: Session = Depends(get_db),
):
    price = crud.get_price(db=db, price_id=price_id)
    if not price:
        raise HTTPException(status_code=404, detail="해당 ID의 가격 데이터를 찾을 수 없습니다.")
    return price

@app.get(
    "/indicators/{stock_id}",
    response_model=schemas.IndicatorSummary,
    summary="기본 기술적 지표 조회",
    description=(
        "특정 종목의 최근 N개 가격 데이터를 바탕으로 "
        "단순 이동평균(5, 20), RSI(14), 3일 모멘텀을 계산해서 반환합니다."
    ),
)
def get_indicators(
    stock_id: int,
    days: int = 60,   # 기본: 최근 60개 데이터(60일이라고 생각해도 됨)
    db: Session = Depends(get_db),
):
    # 1) 종목 존재 여부 확인
    stock = crud.get_stock(db=db, stock_id=stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="해당 ID의 종목을 찾을 수 없습니다.")

    # 2) 가격 데이터 가져오기 (최신 날짜부터 정렬되어 있음)
    prices = crud.list_prices_by_stock(db=db, stock_id=stock_id, skip=0, limit=days)

    if not prices:
        raise HTTPException(status_code=404, detail="해당 종목에 대한 가격 데이터가 없습니다.")

    # 3) 오래된 날짜 → 최신 날짜 순서로 다시 정렬
    prices_sorted = sorted(prices, key=lambda p: p.date)
    closes = [p.close for p in prices_sorted]

    latest = prices_sorted[-1]
    latest_date = latest.date
    latest_close = latest.close

    # 4) 지표 계산
    ma_5 = calc_sma(closes, 5)
    ma_20 = calc_sma(closes, 20)
    rsi_14 = calc_rsi(closes, 14)
    momentum_3d = calc_momentum(closes, 3)

    # 5) 응답 구성
    result = schemas.IndicatorSummary(
        stock_id=stock_id,
        days=len(closes),        # 실제 사용한 데이터 개수
        latest_date=latest_date,
        latest_close=latest_close,
        ma_5=ma_5,
        ma_20=ma_20,
        rsi_14=rsi_14,
        momentum_3d=momentum_3d,
    )
    return result

@app.get(
    "/predict/{stock_id}",
    response_model=schemas.PredictionSummary,
    summary="더미 단기 예측 (상승 확률/기대수익률)",
    description=(
        "최근 가격 데이터와 기본 지표(RSI, 모멘텀)를 이용해서 "
        "단기 상승 확률과 기대 수익률을 간단한 규칙 기반으로 계산합니다. "
        "실제 투자 모델이 아니라 프로토타입용 더미 모델입니다."
    ),
)
def predict_dummy(
    stock_id: int,
    horizon_days: int = 3,  # 며칠 기준으로 수익률을 볼지
    window_days: int = 30,  # 최근 몇 개 가격 데이터를 사용할지
    db: Session = Depends(get_db),
):
    # 1) 종목 존재 여부 확인
    stock = crud.get_stock(db=db, stock_id=stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="해당 ID의 종목을 찾을 수 없습니다.")

    if horizon_days < 1:
        raise HTTPException(status_code=400, detail="horizon_days는 1 이상이어야 합니다.")

    # 2) 최근 가격 데이터 가져오기 (최신 날짜부터)
    prices = crud.list_prices_by_stock(db=db, stock_id=stock_id, skip=0, limit=window_days)
    if len(prices) < horizon_days + 1:
        raise HTTPException(
            status_code=400,
            detail=f"예측에 필요한 최소 데이터({horizon_days + 1}개)보다 가격 데이터가 부족합니다.",
        )

    # 오래된 날짜 → 최신 날짜 순서로 정렬
    prices_sorted = sorted(prices, key=lambda p: p.date)
    closes = [p.close for p in prices_sorted]

    latest = prices_sorted[-1]
    latest_date = latest.date
    latest_close = latest.close

    # 3) 최근 horizon_days 동안의 수익률 계산
    base_price = prices_sorted[-(horizon_days + 1)].close
    if base_price <= 0:
        recent_return = 0.0
    else:
        recent_return = (latest_close - base_price) / base_price  # 예: 0.05 = +5%

    # 4) 보조 지표: RSI14, 3일 모멘텀
    rsi_14 = calc_rsi(closes, 14)
    mom_3d = calc_momentum(closes, 3)

    # 5) 더미 규칙 기반으로 상승 확률 계산
    prob_up = 0.5  # 기본값 50%

    # (1) 최근 수익률이 플러스면 확률 가산, 마이너스면 감소
    # 수익률이 크더라도 영향이 너무 커지지 않도록 0.15 범위로 제한
    prob_up += max(-0.15, min(0.15, recent_return * 2))

    # (2) RSI 기반 조정
    if rsi_14 is not None:
        if rsi_14 < 35:
            # 과매도 구간: 반등 기대 +5%
            prob_up += 0.05
        elif rsi_14 > 70:
            # 과매수 구간: 조정 위험 -5%
            prob_up -= 0.05

    # (3) 3일 모멘텀 기반 조정
    if mom_3d is not None:
        if mom_3d > 0:
            prob_up += 0.03
        elif mom_3d < 0:
            prob_up -= 0.03

    # (4) 확률은 0.05 ~ 0.95 사이로 클램프
    prob_up = max(0.05, min(0.95, prob_up))

    # 6) 기대 수익률(%)을 아주 단순하게 최근 수익률 기준으로 설정
    expected_return_pct = recent_return * 100.0  # 예: recent_return=0.034 -> 3.4(%)

    result = schemas.PredictionSummary(
        stock_id=stock_id,
        horizon_days=horizon_days,
        latest_date=latest_date,
        latest_close=latest_close,
        prob_up=prob_up,
        expected_return=expected_return_pct,
        model_version="dummy_v1",
    )
    return result

@app.get(
    "/stocks/{stock_id}/summary",
    response_model=schemas.StockFullSummary,
    summary="종목 통합 요약",
    description=(
        "종목 기본 정보 + 최신 가격 + 기본 기술적 지표(MA5/MA20/RSI14/3일 모멘텀) "
        "+ 더미 예측(단기 상승 확률/기대수익률)을 한 번에 반환합니다."
    ),
)
def get_stock_full_summary(
    stock_id: int,
    horizon_days: int = 3,   # 예측 기간 (며칠 기준)
    window_days: int = 60,   # 최근 몇 개 가격 데이터 사용할지
    db: Session = Depends(get_db),
):
    # 1) 종목 기본 정보 조회
    stock = crud.get_stock(db=db, stock_id=stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="해당 ID의 종목을 찾을 수 없습니다.")

    # 2) 가격 데이터 조회
    prices = crud.list_prices_by_stock(db=db, stock_id=stock_id, skip=0, limit=window_days)
    if len(prices) < horizon_days + 1:
        raise HTTPException(
            status_code=400,
            detail=f"요약에 필요한 최소 가격 데이터({horizon_days + 1}개)보다 적습니다.",
        )

    # 오래된 날짜 → 최신 날짜 순서로 정렬
    prices_sorted = sorted(prices, key=lambda p: p.date)
    closes = [p.close for p in prices_sorted]

    latest = prices_sorted[-1]
    latest_date = latest.date
    latest_close = latest.close

    # 3) 지표 계산 (indicators.py 재사용)
    ma_5 = calc_sma(closes, 5)
    ma_20 = calc_sma(closes, 20)
    rsi_14 = calc_rsi(closes, 14)
    momentum_3d = calc_momentum(closes, 3)

    # 4) 더미 예측 로직 (predict_dummy와 동일 로직 그대로 사용)

    base_price = prices_sorted[-(horizon_days + 1)].close
    if base_price <= 0:
        recent_return = 0.0
    else:
        recent_return = (latest_close - base_price) / base_price  # 예: 0.05 = +5%

    prob_up = 0.5  # 기본 50%

    # (1) 최근 수익률 기반 조정
    prob_up += max(-0.15, min(0.15, recent_return * 2))

    # (2) RSI 기반 조정
    if rsi_14 is not None:
        if rsi_14 < 35:
            prob_up += 0.05
        elif rsi_14 > 70:
            prob_up -= 0.05

    # (3) 3일 모멘텀 기반 조정
    if momentum_3d is not None:
        if momentum_3d > 0:
            prob_up += 0.03
        elif momentum_3d < 0:
            prob_up -= 0.03

    # (4) 확률 0.05~0.95 사이로 클램프
    prob_up = max(0.05, min(0.95, prob_up))

    # 기대 수익률 (%)
    expected_return_pct = recent_return * 100.0

    # 5) 통합 응답 구성
    summary = schemas.StockFullSummary(
        stock_id=stock.id,
        symbol=stock.symbol,
        name=stock.name,
        market=stock.market,
        sector=stock.sector,
        currency=stock.currency,
        latest_date=latest_date,
        latest_close=latest_close,
        ma_5=ma_5,
        ma_20=ma_20,
        rsi_14=rsi_14,
        momentum_3d=momentum_3d,
        horizon_days=horizon_days,
        prob_up=prob_up,
        expected_return=expected_return_pct,
        model_version="dummy_v1",
    )
    return summary
