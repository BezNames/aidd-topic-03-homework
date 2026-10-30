from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


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


class PriceAlert(models.Model):
    """Персональное условие уведомления о цене акции."""

    ABOVE = "above"
    BELOW = "below"
    DIRECTIONS = ((ABOVE, "Выше или равно"), (BELOW, "Ниже или равно"))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="price_alerts")
    share = models.ForeignKey(
        Share, on_delete=models.CASCADE, related_name="price_alerts"
    )
    target_price = models.DecimalField(max_digits=20, decimal_places=4)
    direction = models.CharField(max_length=5, choices=DIRECTIONS)
    is_active = models.BooleanField(default=True)
    triggered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PriceAlertNotification(models.Model):
    """Единственное уведомление о срабатывании конкретного условия."""

    alert = models.OneToOneField(
        PriceAlert, on_delete=models.CASCADE, related_name="notification"
    )
    triggered_price = models.DecimalField(max_digits=20, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
