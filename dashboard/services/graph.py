from datetime import timedelta, timezone

from plotly.graph_objs import Scatter
from plotly.offline import plot

from config.settings import TINKOFF_TOKEN, logger
from .tinkoff_client import Client, CandleInterval, TinkoffTokenError


def _now_utc():
    return timezone.now()


def get_graph(share):
    try:
        with Client(TINKOFF_TOKEN) as client:
            x_data, y_data = [], []
            for candle in client.get_all_candles(
                figi=share.figi,
                from_=_now_utc() - timedelta(days=180),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
            ):
                if candle.time is None:
                    continue
                x_data.append(candle.time.date())
                y_data.append(float(candle.close.to_decimal))
    except TinkoffTokenError:
        logger.warning(
            "График для акции %s недоступен: не задан TINKOFF_TOKEN", share.figi
        )
        return None
    except Exception as exc:
        logger.error("Ошибка построения графика для акции %s: %s", share.figi, exc)
        return None

    plot_div = plot(
        [
            Scatter(
                x=x_data,
                y=y_data,
                mode="lines",
                name="Курс",
                opacity=0.8,
                marker_color="red",
            )
        ],
        output_type="div",
        show_link=False,
        link_text="",
    )
    return plot_div