from os import environ

from celery import chain

from ..utils import validate
from .tasks import create_donation, create_person


@validate(environ["STRIPE_NATIONBUILDER_WEBHOOK_SECRET"])
def event(charge):
    if charge.get("statement_descriptor_suffix") == "Fundist Donation":
        tasks = []

        if "nationbuilder_person" not in charge["metadata"]:
            tasks.append(create_person.si(charge["id"]))

        if "nationbuilder_donation" not in charge["metadata"]:
            tasks.append(create_donation.si(charge["id"]))

        chain(tasks).delay()
