from django.core.management.base import BaseCommand
from django.db import IntegrityError

from config.settings import TINKOFF_TOKEN, logger
from dashboard.models import Share
from dashboard.services.tinkoff_client import Client, TinkoffTokenError


class Command(BaseCommand):
    help = "Add shares to DB"

    def handle(self, *args, **options):
        try:
            with Client(TINKOFF_TOKEN) as client:
                instruments = client.instruments.shares()
                created, skipped = 0, 0
                for instrument in instruments:
                    try:
                        Share.objects.get_or_create(
                            figi=instrument.figi,
                            defaults={
                                "name": instrument.name or "",
                                "isin": instrument.isin or "",
                                "ticker": instrument.ticker or "",
                                "currency": instrument.currency or "",
                                "uid": instrument.uid or "",
                            },
                        )
                        created += 1
                    except IntegrityError:
                        skipped += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Загружено акций: {created}, пропущено (уже есть): {skipped}"
                    )
                )
        except TinkoffTokenError as exc:
            self.stdout.write(self.style.ERROR(f"Не удалось загрузить акции: {exc}"))
            logger.error("add_shares failed: %s", exc)