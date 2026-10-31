from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from dashboard.models import Share, Watch, WatchNotification
from dashboard.services.watching import check_watches_for_share

User = get_user_model()


class DashboardTests(APITestCase):
    def setUp(self) -> None:
        self.apple_share = Share.objects.create(
            figi="BBG000B9XRY4",
            isin="US0378331005",
            name="Apple",
            ticker="AAPL",
            currency="usd",
            uid="a9eb4238-eba9-488c-b102-b6140fd08e38",
            last_price=100.50,
            is_trend_high=True,
        )

        self.second_company = {
            "figi": "BBG000B9XRY5",
            "isin": "US0378331004",
            "name": "Company_test",
            "ticker": "TESTTEST",
            "currency": "usd",
            "uid": "a9eb4238-eba9-488c-b102-b6140fd08e39",
            "last_price": 1.50,
            "is_trend_high": False,
        }

        self.staff_user = User.objects.create_user(
            email="staff@test.local",
            password="test-password-123",
            is_staff=True,
        )
        self.plain_user = User.objects.create_user(
            email="plain@test.local",
            password="test-password-123",
        )

    # --- HTML-интерфейс ---

    def test_share_list_html(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_list_html_non_staff(self):
        self.client.force_authenticate(self.plain_user)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # --- REST API: чтение (анонимно) ---

    def test_share_list(self):
        response = self.client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        apple_share = response.json().get("results")[0]
        self.assertEqual(apple_share["id"], self.apple_share.id)
        self.assertEqual(apple_share["figi"], self.apple_share.figi)
        self.assertEqual(apple_share["isin"], self.apple_share.isin)
        self.assertEqual(apple_share["name"], self.apple_share.name)
        self.assertEqual(apple_share["ticker"], self.apple_share.ticker)
        self.assertEqual(apple_share["currency"], self.apple_share.currency)

    def test_share_detail(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self.client.get(f"/api/v1/shares/{share_detail['id']}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_share_detail_invalid(self):
        response = self.client.get("/api/v1/shares/2/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- REST API: запись только для персонала ---

    def _staff_client(self):
        self.client.force_authenticate(self.staff_user)
        return self.client

    def _plain_client(self):
        self.client.force_authenticate(self.plain_user)
        return self.client

    def test_share_create_staff(self):
        client = self._staff_client()
        response = client.post("/api/v1/shares/", self.second_company, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["figi"], self.second_company["figi"])
        self.assertEqual(body["name"], self.second_company["name"])
        self.assertEqual(body["ticker"], self.second_company["ticker"])

        response = client.get("/api/v1/shares/")
        self.assertEqual(len(response.data["results"]), 2)

    def test_share_create_plain_forbidden(self):
        response = self.client.post(
            "/api/v1/shares/", self.second_company, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_share_update_staff(self):
        client = self._staff_client()
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = client.put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "id": share_detail["id"],
                "figi": self.apple_share.figi,
                "isin": self.apple_share.isin,
                "name": f"{self.apple_share.name}_test",
                "ticker": self.apple_share.ticker,
                "currency": self.apple_share.currency,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["figi"], self.apple_share.figi)
        self.assertEqual(body["name"], f"{self.apple_share.name}_test")

    def test_share_update_plain_forbidden(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self._plain_client().put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "id": share_detail["id"],
                "figi": self.apple_share.figi,
                "name": f"{self.apple_share.name}_test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_share_update_invalid(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self._staff_client().put(
            f"/api/v1/shares/{share_detail['id']}/",
            {
                "figi": self.apple_share.figi,
                "name": f"{self.apple_share.name}_test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_share_delete_staff(self):
        client = self._staff_client()
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = client.delete(f"/api/v1/shares/{share_detail['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = client.get("/api/v1/shares/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_share_delete_plain_forbidden(self):
        response = self.client.get("/api/v1/shares/")
        share_detail = response.json().get("results")[0]
        response = self._plain_client().delete(
            f"/api/v1/shares/{share_detail['id']}/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_share_delete_invalid(self):
        client = self._staff_client()
        response = client.delete("/api/v1/shares/3/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WatchTests(APITestCase):
    """Тесты персонального мониторинга акций."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@test.local", password="test-password-123"
        )
        self.other_user = User.objects.create_user(
            email="other@test.local", password="test-password-123"
        )
        self.share = Share.objects.create(
            figi="BBG000BST000",
            isin="XS0000000000",
            name="Тестовая компания",
            ticker="TST",
            currency="rub",
            uid="test-uid-000",
            last_price=Decimal("100.50"),
            is_trend_high=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_watch(self):
        response = self.client.post(
            "/api/v1/watches/",
            {
                "share": self.share.id,
                "target_price": "90.00",
                "direction": "lte",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Watch.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            WatchNotification.objects.filter(watch__user=self.user).count(), 0
        )

    def test_create_watch_invalid_price(self):
        for bad_price in ("0", "-5", ""):
            response = self.client.post(
                "/api/v1/watches/",
                {"share": self.share.id, "target_price": bad_price, "direction": "lte"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_watch_duplicate_for_same_share(self):
        self.client.post(
            "/api/v1/watches/",
            {"share": self.share.id, "target_price": "90.00", "direction": "lte"},
            format="json",
        )
        response = self.client.post(
            "/api/v1/watches/",
            {"share": self.share.id, "target_price": "80.00", "direction": "gte"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Watch.objects.filter(user=self.user).count(), 1)

    def test_list_only_own_watches(self):
        Watch.objects.create(
            user=self.other_user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        response = self.client.get("/api/v1/watches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_cannot_access_other_watch(self):
        other_watch = Watch.objects.create(
            user=self.other_user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        response = self.client.get(f"/api/v1/watches/{other_watch.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_watch(self):
        watch = Watch.objects.create(
            user=self.user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        response = self.client.delete(f"/api/v1/watches/{watch.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Watch.objects.filter(id=watch.id).exists())

    def test_cannot_delete_other_watch(self):
        other_watch = Watch.objects.create(
            user=self.other_user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        response = self.client.delete(f"/api/v1/watches/{other_watch.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Watch.objects.filter(id=other_watch.id).exists())

    def test_notification_created_on_price_match(self):
        Watch.objects.create(
            user=self.user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        self.share.last_price = Decimal("100")
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        self.assertEqual(WatchNotification.objects.filter(watch__user=self.user).count(), 1)
        response = self.client.get("/api/v1/watch-notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_notification_not_duplicated(self):
        watch = Watch.objects.create(
            user=self.user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        self.share.last_price = Decimal("100")
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        check_watches_for_share(self.share)
        self.assertEqual(WatchNotification.objects.filter(watch=watch).count(), 1)

    def test_reset_then_new_crossing_creates_notification(self):
        watch = Watch.objects.create(
            user=self.user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        self.share.last_price = Decimal("100")
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        self.assertEqual(WatchNotification.objects.filter(watch=watch).count(), 1)

        self.share.last_price = Decimal("40")
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        watch.refresh_from_db()
        self.assertIsNone(watch.last_triggered)

        self.share.last_price = Decimal("100")
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        self.assertEqual(WatchNotification.objects.filter(watch=watch).count(), 2)

    def test_lte_direction_triggered(self):
        Watch.objects.create(
            user=self.user,
            share=self.share,
            target_price=Decimal("200"),
            direction="lte",
        )
        self.share.last_price = Decimal("100")
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        self.assertEqual(WatchNotification.objects.filter(watch__user=self.user).count(), 1)

    def test_no_notification_without_price(self):
        Watch.objects.create(
            user=self.user,
            share=self.share,
            target_price=Decimal("50"),
            direction="gte",
        )
        self.share.last_price = None
        self.share.save(update_fields=["last_price"])
        check_watches_for_share(self.share)
        self.assertEqual(WatchNotification.objects.filter(watch__user=self.user).count(), 0)