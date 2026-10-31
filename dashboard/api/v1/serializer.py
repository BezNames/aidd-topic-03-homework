from rest_framework import serializers

from dashboard.models import Share, Watch, WatchNotification


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


class WatchSerializer(serializers.ModelSerializer):
    share_name = serializers.CharField(source="share.name", read_only=True)
    share_ticker = serializers.CharField(source="share.ticker", read_only=True)
    share_last_price = serializers.DecimalField(
        source="share.last_price",
        max_digits=14,
        decimal_places=4,
        read_only=True,
    )

    class Meta:
        model = Watch
        fields = (
            "id",
            "share",
            "share_name",
            "share_ticker",
            "share_last_price",
            "target_price",
            "direction",
            "created_at",
            "last_triggered",
        )
        read_only_fields = ("created_at", "last_triggered")

    def validate_target_price(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError(
                "Целевая цена должна быть положительным числом."
            )
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        share = attrs.get("share")
        if share is not None:
            exclude_pk = self.instance.pk if self.instance else None
            exists = Watch.objects.filter(user=user, share=share)
            if exclude_pk is not None:
                exists = exists.exclude(pk=exclude_pk)
            if exists.exists():
                raise serializers.ValidationError(
                    "У вас уже есть наблюдение за этой акцией."
                )
        return attrs


class WatchNotificationSerializer(serializers.ModelSerializer):
    watch_share = serializers.CharField(
        source="watch.share.ticker", read_only=True
    )
    watch_target_price = serializers.DecimalField(
        source="watch.target_price", max_digits=14, decimal_places=4, read_only=True
    )
    watch_direction = serializers.CharField(
        source="watch.get_direction_display", read_only=True
    )

    class Meta:
        model = WatchNotification
        fields = (
            "id",
            "watch",
            "watch_share",
            "watch_target_price",
            "watch_direction",
            "message",
            "triggered_at",
        )
