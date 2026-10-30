from decimal import Decimal

from config.celery import app
from dashboard.models import PriceAlert, PriceAlertNotification, Share
from dashboard.services.market_data import get_last_data
from config.settings import logger
from django.db import transaction
from django.utils import timezone


def evaluate_price_alerts(share):
    if share.last_price is None:
        return

    current_price = Decimal(str(share.last_price))
    with transaction.atomic():
        alerts = PriceAlert.objects.select_for_update().filter(
            share=share, is_active=True, triggered_at__isnull=True
        )
        for alert in alerts:
            reached = (
                current_price >= alert.target_price
                if alert.direction == PriceAlert.ABOVE
                else current_price <= alert.target_price
            )
            if not reached:
                continue

            notification, created = PriceAlertNotification.objects.get_or_create(
                alert=alert, defaults={"triggered_price": current_price}
            )
            if created:
                alert.triggered_at = timezone.now()
                alert.save(update_fields=["triggered_at"])


@app.task
def update_last_price():
    shares = Share.objects.all()

    for share in shares:
        try:
            [last_price, detetime] = get_last_data(share)

            try:
                if share.last_price > last_price:
                    is_trend_high = False
                else:
                    is_trend_high = True
            except Exception as e:
                logger.error(e)
                is_trend_high = True

            Share.objects.filter(id=share.id).update(
                last_price=last_price, is_trend_high=is_trend_high
            )
            share.last_price = last_price
            evaluate_price_alerts(share)
        except Exception as e:
            logger.error(e)
