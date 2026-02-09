from os import environ

from ..utils import validate
from .tasks import update_charge


@validate(environ["STRIPE_INVOICES_WEBHOOK_SECRET"])
def event(invoice):
    for item in invoice.get("lines", {}).get("data", []):
        if item.get("price", {}).get("product") == environ["STRIPE_PRODUCT_ID"]:
            update_charge.delay(invoice["id"])
            break
