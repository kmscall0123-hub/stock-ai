from pydantic import BaseModel
from datetime import date

# 공통 필드 (내부 코드용 필드 이름은 영어, 의미는 한글로 이해)
class StockBase(BaseModel):
    symbol: str      # 종목코드 (예: 005930.KS)
    name: str        # 종목명 (예: 삼성전자)
    market: str      # 시장 (KOSPI, KOSDAQ, NASDAQ 등)
    sector: str | None = None   # 섹터 (IT, 2차전지, 자동차 등)
    currency: str = "KRW"       # 통화


# 생성 요청에 사용할 스키마
class StockCreate(StockBase):
    pass


# 조회 응답용 스키마
class StockRead(StockBase):
    id: int  # 내부 식별자

    class Config:
        orm_mode = True

# ---------- 가격 스키마 추가 ----------

class PriceBase(BaseModel):
    stock_id: int        # 어느 종목의 가격인지 (stocks.id)
    date: date           # 날짜 (일단 일봉 기준)
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class PriceCreate(PriceBase):
    """가격 생성 요청에 사용할 스키마"""
    pass


class PriceRead(PriceBase):
    """가격 조회 응답용 스키마"""
    id: int

    class Config:
        orm_mode = True


# ---------- 지표(Indicator) 응답용 스키마 ----------

class IndicatorSummary(BaseModel):
    stock_id: int            # 어떤 종목인지 (stocks.id)
    days: int                # 최근 며칠 데이터를 기준으로 계산했는지
    latest_date: date | None # 가장 최근 데이터 날짜
    latest_close: float | None  # 가장 최근 종가

    ma_5: float | None       # 5일 단순 이동평균
    ma_20: float | None      # 20일 단순 이동평균
    rsi_14: float | None     # 14일 RSI
    momentum_3d: float | None  # 3영업일 모멘텀 (수익률 비율)

    class Config:
        orm_mode = False  # ORM 객체가 아니라 계산 결과라서 False여도 상관 없음



# ---------- 예측(Prediction) 응답용 스키마 ----------

class PredictionSummary(BaseModel):
    stock_id: int          # 종목 ID
    horizon_days: int      # 예측 기간 (며칠 기준인지)
    latest_date: date | None   # 기준이 되는 가장 최근 가격 날짜
    latest_close: float | None # 기준이 되는 가장 최근 종가

    prob_up: float         # 상승 확률 (0~1)
    expected_return: float # 기대수익률 (% 단위, 예: 3.5면 +3.5%)

    model_version: str     # 모델 버전 (나중에 실제 모델로 바꿀 때 유용)

    class Config:
        orm_mode = False

# ---------- 종목 통합 요약 응답 스키마 ----------

class StockFullSummary(BaseModel):
    # 종목 기본 정보
    stock_id: int
    symbol: str
    name: str
    market: str
    sector: str | None = None
    currency: str

    # 최신 가격
    latest_date: date | None
    latest_close: float | None

    # 지표
    ma_5: float | None
    ma_20: float | None
    rsi_14: float | None
    momentum_3d: float | None

    # 예측
    horizon_days: int
    prob_up: float
    expected_return: float
    model_version: str
