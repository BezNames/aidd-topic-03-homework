from rest_framework import routers

from .views import (
    PriceAlertNotificationViewSet,
    PriceAlertViewSet,
    ShareViewSet,
)

router = routers.DefaultRouter()
router.register(r"shares", ShareViewSet)
router.register(r"price-alerts", PriceAlertViewSet, basename="price-alert")
router.register(
    r"price-alert-notifications",
    PriceAlertNotificationViewSet,
    basename="price-alert-notification",
)
