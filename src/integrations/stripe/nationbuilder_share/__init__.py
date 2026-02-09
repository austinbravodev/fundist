from os import environ

from celery import chain

from ..utils import validate
from .tasks import create_donation, create_person


@validate(environ["STRIPE_NATIONBUILDER_SHARE_WEBHOOK_SECRET"])
def event(charge):
    if (
        charge.get("statement_descriptor_suffix") == "Fundist Donation"
        and "fundist_share" in charge["metadata"]
    ):
        tasks = []

        if "nationbuilder_share_person" not in charge["metadata"]:
            tasks.append(create_person.si(charge["id"]))

        if "nationbuilder_share_donation" not in charge["metadata"]:
            tasks.append(create_donation.si(charge["id"]))

        chain(tasks).delay()
