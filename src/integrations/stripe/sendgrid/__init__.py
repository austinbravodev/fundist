from os import environ

from ..utils import validate
from .tasks import create_receipt


@validate(environ["STRIPE_SENDGRID_WEBHOOK_SECRET"])
def event(charge):
    if "fundist_receipt" not in charge["metadata"]:
        create_receipt.delay(charge["id"])
