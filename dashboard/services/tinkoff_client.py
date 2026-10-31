"""Минимальный REST-клиент Tinkoff Invest API v1.

Официальный SDK ``tinkoff-investments`` (бета-версия 2023 года) не
распространяется на PyPI (пакет недоступен, см. ANALYSIS.md п.15 и
AGENTS_REPORT.md п.«Ошибки и проблемы»), поэтому приложение заменяет
его этим клиентом. Он реализует ровно те операции, которые нужны
приложению, и возвращает данные в той же структуре, что и SDK:

* ``client.market_data.get_last_prices(figi=[...])`` →
  ``.last_prices`` c элементами ``.price.units``, ``.time``;
* ``client.get_all_candles(figi=..., from_=..., interval=...)`` →
  свечи с ``.time.date()``, ``.close.units``;
* ``client.instruments.shares()`` → ``.instruments`` с ``.figi``,
  ``.name``, ``.isin``, ``.ticker``, ``.currency``, ``.uid``.

Цены отдаются как объект с ``.units`` (целая часть) и ``.nanos``
(дробная часть); для полного значения используйте ``.to_decimal()``.
"""
import enum
import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Iterable, Iterator, List, Optional

import requests

from config.settings import TINKOFF_TOKEN, logger

API_BASE = "https://api-invest.tinkoff.ru/v1"
REQUEST_TIMEOUT = 30


class _Price:
    __slots__ = ("units", "nanos", "_value")

    def __init__(self, units, nanos=0):
        self.units = int(units)
        self.nanos = int(nanos)
        self._value = Decimal(self.units) + Decimal(self.nanos) / Decimal(10 ** 9)

    @property
    def to_decimal(self) -> Decimal:
        return self._value

    def __float__(self):
        return float(self._value)

    def __repr__(self):
        return f"Price(units={self.units}, nanos={self.nanos})"


class _LastPrice:
    __slots__ = ("figi", "price", "time")

    def __init__(self, figi=None, price=None, time=None):
        self.figi = figi
        self.price = price if isinstance(price, _Price) else _Price(0, 0)
        self.time = time


class _Candle:
    __slots__ = ("time", "close", "open", "high", "low", "volume")

    def __init__(self, time=None, close=None, open=None, high=None, low=None, volume=None):
        self.time = time
        self.close = close if isinstance(close, _Price) else _Price(0, 0)
        self.open = open if isinstance(open, _Price) else _Price(0, 0)
        self.high = high if isinstance(high, _Price) else _Price(0, 0)
        self.low = low if isinstance(low, _Price) else _Price(0, 0)
        self.volume = volume


class _Instrument:
    __slots__ = ("figi", "isin", "name", "ticker", "currency", "uid", "type", "exchange")

    def __init__(self, figi=None, isin=None, name=None, ticker=None,
                 currency=None, uid=None, type=None, exchange=None):
        self.figi = figi
        self.isin = isin
        self.name = name
        self.ticker = ticker
        self.currency = currency
        self.uid = uid
        self.type = type
        self.exchange = exchange


class CandleInterval(enum.Enum):
    CANDLE_INTERVAL_UNSPECIFIED = 0
    CANDLE_INTERVAL_1_MIN = 60
    CANDLE_INTERVAL_2_MIN = 120
    CANDLE_INTERVAL_3_MIN = 180
    CANDLE_INTERVAL_5_MIN = 300
    CANDLE_INTERVAL_10_MIN = 600
    CANDLE_INTERVAL_15_MIN = 900
    CANDLE_INTERVAL_30_MIN = 1800
    CANDLE_INTERVAL_HOUR = 3600
    CANDLE_INTERVAL_DAY = 86400
    CANDLE_INTERVAL_WEEK = 7 * 86400
    CANDLE_INTERVAL_MONTH = 30 * 86400


class _MarketData:
    def __init__(self, client):
        self._client = client

    def get_last_prices(self, figi: List[str]) -> List[_LastPrice]:
        payload = self._client._request(
            "/market-data/get-last-prices",
            {"figi": figi},
        )
        raw_prices = payload.get("lastPrices") if isinstance(payload, dict) else None
        if not raw_prices:
            return []
        result = []
        for raw in raw_prices:
            if not isinstance(raw, dict):
                continue
            raw_price = raw.get("price")
            price = _build_price(raw_price)
            result.append(_LastPrice(
                figi=raw.get("figi"),
                price=price,
                time=_build_time(raw.get("time")),
            ))
        return result


class _Instruments:
    def __init__(self, client):
        self._client = client

    def shares(self) -> List[_Instrument]:
        payload = self._client._request("/instruments/all", {"instrumentStatus": 0})
        raw_instruments = payload.get("instruments") if isinstance(payload, dict) else None
        if not raw_instruments:
            return []
        result = []
        for raw in raw_instruments:
            if not isinstance(raw, dict):
                continue
            instrument_type = raw.get("type")
            if instrument_type and instrument_type != "Share":
                continue
            result.append(_Instrument(
                figi=raw.get("figi"),
                isin=raw.get("isin"),
                name=raw.get("name"),
                ticker=raw.get("ticker"),
                currency=raw.get("currency"),
                uid=raw.get("uid"),
                type=instrument_type,
                exchange=raw.get("exchange"),
            ))
        return result


class Client:
    """HTTP-клиент Tinkoff Invest API. Поддерживает контекстный менеджер."""

    def __init__(self, token: str = TINKOFF_TOKEN):
        if not token:
            raise TinkoffTokenError(
                "Отсутствует TINKOFF_TOKEN: задайте переменную окружения "
                "TINKOFF_TOKEN или значение TINKOFF_TOKEN в config/settings.py"
            )
        self._token = token
        self.market_data = _MarketData(self)
        self.instruments = _Instruments(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def get_all_candles(
        self,
        figi: str,
        from_,
        interval: CandleInterval,
    ) -> Iterator[_Candle]:
        payload = self._request(
            "/candles/get-all",
            {
                "figi": figi,
                "from": _format_time(from_),
                "interval": interval.value,
            },
        )
        raw_candles = payload.get("candles") if isinstance(payload, dict) else None
        if raw_candles is None:
            raw_candles = payload if isinstance(payload, list) else []
        for raw in raw_candles:
            if isinstance(raw, dict):
                inner = raw.get("candle") if "candle" in raw else raw
                if not isinstance(inner, dict):
                    continue
                yield _Candle(
                    time=_build_time(inner.get("time")),
                    close=_build_price(inner.get("close")),
                    open=_build_price(inner.get("open")),
                    high=_build_price(inner.get("high")),
                    low=_build_price(inner.get("low")),
                    volume=inner.get("volume"),
                )

    def _request(self, path: str, body: dict) -> dict:
        url = f"{API_BASE}{path}"
        try:
            response = requests.post(
                url,
                json=body,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error("Tinkoff request to %s failed: %s", url, exc)
            raise TinkoffAPIError(f"Tinkoff request to {url} failed: {exc}") from exc
        if response.status_code >= 400:
            logger.error(
                "Tinkoff API error %s for %s: %s",
                response.status_code,
                url,
                response.text[:500],
            )
            raise TinkoffAPIError(
                f"Tinkoff API error {response.status_code} for {url}: "
                f"{response.text[:200]}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            logger.error("Invalid JSON in Tinkoff response for %s: %s", url, exc)
            raise TinkoffAPIError(f"Invalid JSON in Tinkoff response for {url}") from exc
        if not isinstance(data, dict):
            return {}
        payload = data.get("payload")
        if isinstance(payload, dict):
            return payload
        return data


class TinkoffTokenError(ValueError):
    """Отсутствует токен Tinkoff Invest."""


class TinkoffAPIError(RuntimeError):
    """Ошибка на стороне Tinkoff Invest API."""


def _build_price(raw) -> _Price:
    if raw is None:
        return _Price(0, 0)
    if isinstance(raw, dict):
        return _Price(raw.get("units", 0), raw.get("nanos", 0))
    try:
        return _Price(int(raw))
    except (TypeError, ValueError):
        try:
            value = Decimal(str(raw))
            return _Price(int(value), 0)
        except (InvalidOperation, ValueError):
            return _Price(0, 0)


def _build_time(raw) -> Optional[datetime]:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    text = str(raw).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _format_time(value: datetime) -> str:
    return value.isoformat()