from os import environ

from ..utils import validate
from .tasks import update_progress


@validate(environ["STRIPE_DATABASE_WEBHOOK_SECRET"])
def event(charge):
    if charge["description"] and "database" not in charge["metadata"]:
        update_progress.delay(charge["id"])
