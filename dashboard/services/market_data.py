from config.settings import TINKOFF_TOKEN, logger
from .tinkoff_client import Client, TinkoffAPIError


def get_last_data(share):
    with Client(TINKOFF_TOKEN) as client:
        last_prices = client.market_data.get_last_prices(figi=[share.figi])
        if not last_prices:
            raise TinkoffAPIError(
                f"Tinkoff вернул пустой список цен для акции {share.figi}"
            )
        resp = last_prices.pop()
        logger.info("Get last data for share with id %s: %s", share.id, resp.price)
        return [resp.price.to_decimal, resp.time]