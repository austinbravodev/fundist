import time
from os import environ

from database import Session
from database.models import Progress
from quart import current_app
from sqlalchemy.future import select


# async def exchange_rate(base, symbol):
#     return (
#         await (
#             await current_app.cached_client.get(
#                 "https://theforexapi.com/api/latest",
#                 params={"base": base, "symbols": symbol},
#             )
#         ).json(content_type="text/json")
#     )["rates"][symbol]


async def exchange_rate(base, symbol):
    return (
        await (
            await current_app.cached_client.get(
                "https://api.currencyapi.com/v3/latest",
                params={
                    "apikey": environ["CURRENCYAPI_KEY"],
                    "base_currency": base,
                    "currencies": symbol,
                },
            )
        ).json(content_type="text/json")
    )["data"][symbol]["value"]


async def cache_progress(tag):
    if (
        tag not in current_app.config["CACHE"]["PROGRESS"][0]
        or time.time() - current_app.config["CACHE"]["PROGRESS"][0][tag][0]
        > current_app.config["CACHE"]["PROGRESS"][1]
    ):
        async with Session() as db:
            current_app.config["CACHE"]["PROGRESS"][0][tag] = (
                time.time(),
                (await db.execute(select(Progress).filter_by(tag=tag)))
                .scalars()
                .fetchall(),
            )

    return current_app.config["CACHE"]["PROGRESS"][0][tag][1]
