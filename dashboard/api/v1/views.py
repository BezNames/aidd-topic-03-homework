from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from dashboard.models import Share, Watch, WatchNotification
from dashboard.api.permissions import IsStaffOrReadOnly

from .serializer import ShareSerializer, WatchNotificationSerializer, WatchSerializer


class ShareFilter(filters.FilterSet):
    class Meta:
        model = Share
        fields = ("name", "ticker")


class ShareViewSet(viewsets.ModelViewSet):
    serializer_class = ShareSerializer
    queryset = Share.objects.all()
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend, SearchFilter)
    filterset_class = ShareFilter
    ordering_fields = ["name", "ticker"]
    search_fields = ["$name"]


class WatchViewSet(viewsets.ModelViewSet):
    serializer_class = WatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Watch.objects.filter(user=self.request.user)
            .select_related("share")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WatchNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WatchNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            WatchNotification.objects.filter(watch__user=self.request.user)
            .select_related("watch__share")
        )
