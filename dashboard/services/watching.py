"""Логика персонального мониторинга цен."""

from django.db import transaction
from django.utils import timezone

from config.settings import logger
from dashboard.models import Watch, WatchNotification


def check_watches_for_share(share):
    """Проверить наблюдения за акцией и создать уведомления по условиям.

    Условие срабатывания:
    * ``gte`` — цена >= целевой;
    * ``lte`` — цена <= целевой.

    Дедупликация: наблюдение запоминает время последнего срабатывания в
    ``last_triggered``. Пока цена держится в срабатывшем состоянии,
    повторные проверки не создают дубликаты. Когда цена уходит от
    условия, ``last_triggered`` сбрасывается и следующее пересечение
    создаст новое уведомление.
    """
    if share.last_price is None:
        return
    for watch in Watch.objects.filter(share=share).select_related("user"):
        if _triggered(watch, share.last_price):
            _on_triggered(watch)
        else:
            _reset(watch)


def _triggered(watch: Watch, last_price) -> bool:
    if watch.direction == "gte":
        return last_price >= watch.target_price
    return last_price <= watch.target_price


@transaction.atomic
def _on_triggered(watch: Watch):
    if watch.last_triggered is not None:
        return
    share = watch.share
    WatchNotification.objects.create(
        watch=watch,
        message=(
            f"Цена {share.ticker} достигла цели: {share.last_price} "
            f"({watch.get_direction_display()})"
        ),
    )
    watch.last_triggered = timezone.now()
    watch.save(update_fields=["last_triggered"])
    logger.info(
        "Наблюдение %s сработало (цена %s)", watch.id, share.ticker
    )


@transaction.atomic
def _reset(watch: Watch):
    if watch.last_triggered is not None:
        watch.last_triggered = None
        watch.save(update_fields=["last_triggered"])