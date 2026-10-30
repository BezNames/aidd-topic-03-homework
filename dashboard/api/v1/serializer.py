from rest_framework import serializers

from dashboard.models import PriceAlert, PriceAlertNotification, Share


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = (
            "id",
            "figi",
            "isin",
            "name",
            "ticker",
            "currency",
            "last_price",
            "is_trend_high",
            "updated_at",
        )


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = (
            "id",
            "share",
            "target_price",
            "direction",
            "is_active",
            "triggered_at",
            "created_at",
        )
        read_only_fields = ("id", "triggered_at", "created_at")


class PriceAlertNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlertNotification
        fields = ("id", "alert", "triggered_price", "created_at")
        read_only_fields = fields
