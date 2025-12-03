"""
가격 리스트(종가 배열)를 기반으로 기본적인 기술적 지표를 계산하는 모듈.

- 단순 이동평균 (SMA)
- 모멘텀 (최근 수익률)
- RSI(14) (Wilder 방식 근사)
"""

from collections.abc import Sequence
from typing import Optional


def calc_sma(values: Sequence[float], window: int) -> Optional[float]:
    """
    단순 이동평균 (Simple Moving Average)

    values: 오래된 값 → 최신 값 순서의 리스트
    window: 몇 개 기간의 평균을 낼지 (예: 5, 20)

    충분한 데이터가 없으면 None 반환
    """
    if len(values) < window:
        return None
    slice_values = values[-window:]
    return sum(slice_values) / window


def calc_momentum(closes: Sequence[float], period: int) -> Optional[float]:
    """
    모멘텀: (마지막 종가 - n일 전 종가) / n일 전 종가

    예: period=3 이면, (마지막 - 3일 전) / 3일 전
    """
    if len(closes) < period + 1:
        return None

    base_price = closes[-period - 1]
    last_price = closes[-1]

    if base_price == 0:
        return None

    return (last_price - base_price) / base_price


def calc_rsi(closes: Sequence[float], period: int = 14) -> Optional[float]:
    """
    RSI(상대강도지수) 계산 (Wilder 방식 근사)

    closes: 오래된 값 → 최신 값 순서의 종가 리스트
    period: 기본 14

    데이터가 부족하면 None 반환
    """
    if len(closes) < period + 1:
        return None

    # 종가 변화량 리스트 계산
    changes = []
    for i in range(1, len(closes)):
        changes.append(closes[i] - closes[i - 1])

    # 초기 평균 상승/하락 (첫 period 구간)
    gains = []
    losses = []
    for ch in changes[:period]:
        if ch > 0:
            gains.append(ch)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-ch)

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # 이후부터는 Wilder 이동평균 방식으로 업데이트
    for ch in changes[period:]:
        gain = ch if ch > 0 else 0.0
        loss = -ch if ch < 0 else 0.0

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        # 손실이 거의 없으면 RSI = 100
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi
