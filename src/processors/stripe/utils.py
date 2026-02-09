from os import environ

from aiohttp import BasicAuth


URL = "https://api.stripe.com/v1/"

_PARAMS = {
    "auth": BasicAuth(environ["STRIPE_KEY"]),
    "headers": {"Stripe-Version": "2020-08-27"},
}
