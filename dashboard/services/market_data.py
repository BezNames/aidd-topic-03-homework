from config.settings import TINKOFF_TOKEN, logger


def get_last_data(share):
    if not TINKOFF_TOKEN:
        raise RuntimeError("TINKOFF_TOKEN is not configured")

    from tinkoff.invest import Client

    with Client(TINKOFF_TOKEN) as client:
        resp = client.market_data.get_last_prices(figi=[share.figi])
        if not resp.last_prices:
            raise RuntimeError(f"No market data returned for FIGI {share.figi}")
        resp = resp.last_prices[0]
        logger.info(f"Get last data for share with id {share.id}")
        return [resp.price.units, resp.time]
