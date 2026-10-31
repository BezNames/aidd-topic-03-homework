from django.urls import include, path

from dashboard.views import (
    ShareCreateView,
    ShareDeleteView,
    ShareDetailView,
    ShareListView,
    ShareUpdateView,
    WatchCreateView,
    WatchDeleteView,
    WatchListView,
    WatchNotificationListView,
)

app_name = "dashboard"

urlpatterns = [
    path("", ShareListView.as_view(), name="index"),
    path("watches/", WatchListView.as_view(), name="watch-index"),
    path("watches/create/", WatchCreateView.as_view(), name="watch-create"),
    path("watches/<int:pk>/delete/", WatchDeleteView.as_view(), name="watch-delete"),
    path(
        "watches/notifications/",
        WatchNotificationListView.as_view(),
        name="watch-notifications",
    ),
    path("<int:pk>", ShareDetailView.as_view(), name="detail"),
    path("create", ShareCreateView.as_view(), name="create"),
    path("update/<int:pk>", ShareUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", ShareDeleteView.as_view(), name="delete"),
    path("api/", include("dashboard.api.urls")),
]
