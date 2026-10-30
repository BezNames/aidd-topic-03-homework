from django.contrib import admin

from dashboard.models import PriceAlert, PriceAlertNotification, Share


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("figi", "isin", "name", "ticker", "currency")
    search_fields = ("figi", "isin", "name", "ticker")
    fields = (
        "figi",
        "isin",
        "name",
        "ticker",
        "currency",
        "uid",
        "last_price",
        "is_trend_high",
    )


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "share",
        "target_price",
        "direction",
        "is_active",
        "triggered_at",
    )
    list_filter = ("direction", "is_active")
    search_fields = ("user__username", "share__ticker", "share__name")


@admin.register(PriceAlertNotification)
class PriceAlertNotificationAdmin(admin.ModelAdmin):
    list_display = ("alert", "triggered_price", "created_at")
