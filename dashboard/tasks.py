from config.celery import app
from dashboard.models import Share
from dashboard.services.market_data import get_last_data
from dashboard.services.watching import check_watches_for_share
from config.settings import logger


@app.task
def update_last_price():
    for share in Share.objects.all().iterator():
        try:
            last_price, detetime = get_last_data(share)
        except Exception as exc:
            logger.error(
                "Не удалось получить цену для акции %s (id=%s): %s",
                share.figi,
                share.id,
                exc,
            )
            continue

        try:
            if share.last_price is not None and last_price is not None:
                is_trend_high = last_price >= share.last_price
            else:
                is_trend_high = True
            share.last_price = last_price
            share.is_trend_high = is_trend_high
            share.save(update_fields=["last_price", "is_trend_high"])
            check_watches_for_share(share)
        except Exception as exc:
            logger.error(
                "Не удалось обновить цену для акции %s (id=%s): %s",
                share.figi,
                share.id,
                exc,
            )