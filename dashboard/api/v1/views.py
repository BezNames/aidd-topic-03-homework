from django_filters import rest_framework as filters
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from dashboard.models import PriceAlert, PriceAlertNotification, Share

from .serializer import (
    PriceAlertNotificationSerializer,
    PriceAlertSerializer,
    ShareSerializer,
)


class ShareFilter(filters.FilterSet):
    class Meta:
        model = Share
        fields = ("name", "ticker")


class ShareViewSet(viewsets.ModelViewSet):
    serializer_class = ShareSerializer
    queryset = Share.objects.all()
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend, SearchFilter)
    filterset_class = ShareFilter
    ordering_fields = ["name", "ticker"]
    search_fields = ["$name"]


class PriceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceAlertSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user).select_related("share")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PriceAlertNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PriceAlertNotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return PriceAlertNotification.objects.filter(
            alert__user=self.request.user
        ).select_related("alert", "alert__share")
