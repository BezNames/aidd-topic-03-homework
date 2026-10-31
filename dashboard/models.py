from django.conf import settings
from django.db import models


WATCH_DIRECTIONS = (
    ("gte", "Цена выше или равна"),
    ("lte", "Цена ниже или равна"),
)


class Share(models.Model):
    """Акция"""

    figi = models.CharField(max_length=255, unique=True)
    isin = models.CharField(max_length=255)
    name = models.CharField(max_length=255, verbose_name="Наименование компании")
    ticker = models.CharField(max_length=10, unique=True, verbose_name="Тикер")
    currency = models.CharField(max_length=20, verbose_name="Валюта")
    uid = models.CharField(max_length=255, unique=True)
    last_price = models.FloatField(blank=True, null=True, verbose_name="Текущая цена")
    is_trend_high = models.BooleanField(
        blank=True, null=True, verbose_name="Растет цена"
    )
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return f"{self.name} ({self.ticker})"


class Watch(models.Model):
    """Наблюдение пользователя за ценой акции."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watches",
        verbose_name="Пользователь",
    )
    share = models.ForeignKey(
        Share,
        on_delete=models.CASCADE,
        related_name="watches",
        verbose_name="Акция",
    )
    target_price = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        verbose_name="Целевая цена",
    )
    direction = models.CharField(
        max_length=5,
        choices=WATCH_DIRECTIONS,
        verbose_name="Направление сравнения",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Создано"
    )
    last_triggered = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последнее срабатывание условия",
    )

    class Meta:
        verbose_name = "Наблюдение"
        verbose_name_plural = "Наблюдения"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "share"], name="unique_user_share_watch"
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.email} → {self.share.ticker} "
            f"({self.get_direction_display()}) @ {self.target_price}"
        )


class WatchNotification(models.Model):
    """Уведомление о выполнении условия наблюдения."""

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Наблюдение",
    )
    message = models.TextField(verbose_name="Текст уведомления")
    triggered_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Сработало"
    )

    class Meta:
        verbose_name = "Уведомление наблюдения"
        verbose_name_plural = "Уведомления наблюдений"
        ordering = ["-triggered_at"]

    def __str__(self):
        return f"Уведомление для {self.watch} ({self.triggered_at})"
