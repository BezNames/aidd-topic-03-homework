from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from .forms import ShareModelForm, WatchModelForm
from .models import Share, Watch
from .services.graph import get_graph


class IsUserAuthenticatedMixin(UserPassesTestMixin):
    """Доступ только для аутентифицированных пользователей."""

    def test_func(self):
        return self.request.user.is_authenticated

    @staticmethod
    def handle_no_permission():
        return redirect("dashboard:index")


class IsStaffRequiredMixin(UserPassesTestMixin):
    """Доступ только для персонала (суперпользователей/админов)."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    @staticmethod
    def handle_no_permission():
        return redirect("dashboard:index")


class WatchListView(ListView):
    """Список наблюдений пользователя (только свои)."""

    model = Watch
    template_name = "dashboard/watch_list.html"
    paginate_by = 50
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Watch.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        return queryset.select_related("share")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from dashboard.models import WatchNotification

        if self.request.user.is_authenticated:
            context["notifications_count"] = (
                WatchNotification.objects.filter(watch__user=self.request.user).count()
            )
        else:
            context["notifications_count"] = 0
        return context


class WatchCreateView(IsUserAuthenticatedMixin, CreateView):
    """Добавление наблюдения за акцией."""

    template_name = "dashboard/watch_create.html"
    form_class = WatchModelForm
    success_url = reverse_lazy("dashboard:watch-index")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class WatchDeleteView(IsUserAuthenticatedMixin, DeleteView):
    """Удаление наблюдения (только своё)."""

    model = Watch
    template_name = "dashboard/watch_delete.html"
    success_url = reverse_lazy("dashboard:watch-index")

    def get_queryset(self):
        return Watch.objects.filter(user=self.request.user)


class WatchNotificationListView(ListView):
    """Уведомления пользователя (только свои)."""

    template_name = "dashboard/watch_notifications.html"
    paginate_by = 50
    ordering = ["-triggered_at"]

    def get_queryset(self):
        return (
            Watch.objects.filter(user=self.request.user)
            .select_related("notifications")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notifications"] = (
            WatchNotificationListView._get_notifications(self.request.user)
        )
        return context

    @staticmethod
    def _get_notifications(user):
        from dashboard.models import WatchNotification

        return WatchNotification.objects.filter(
            watch__user=user
        ).select_related("watch__share")


class ShareListView(ListView):
    """Список акций"""

    model = Share
    template_name = "dashboard/list.html"
    paginate_by = 100
    ordering = ["name"]


class ShareDetailView(View):
    @staticmethod
    def get(request, pk):
        share = get_object_or_404(Share.objects.all(), id=pk)

        return render(
            request,
            "dashboard/detail.html",
            {"plot_div": get_graph(share), "share": share},
        )


class ShareCreateView(IsStaffRequiredMixin, CreateView):
    """Добавление инструмента"""

    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareUpdateView(IsStaffRequiredMixin, UpdateView):
    """Редактирование инструмента"""

    model = Share
    template_name = "dashboard/create.html"
    form_class = ShareModelForm
    success_url = reverse_lazy("dashboard:index")


class ShareDeleteView(IsStaffRequiredMixin, DeleteView):
    """Удаление инструмента"""

    model = Share
    template_name = "dashboard/delete.html"
    success_url = reverse_lazy("dashboard:index")