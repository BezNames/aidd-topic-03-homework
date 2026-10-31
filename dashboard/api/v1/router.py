from rest_framework import routers

from .views import ShareViewSet, WatchViewSet, WatchNotificationViewSet

router = routers.DefaultRouter()
router.register(r"shares", ShareViewSet)
router.register(r"watches", WatchViewSet, basename="watch")
router.register(
    r"watch-notifications", WatchNotificationViewSet, basename="watch-notification"
)