import os

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from database import Session

from .utils import Client


MODS = []

for plats in filter(None, os.environ.get("INTEGRATIONS", "").split(",")):
    origin, dests = plats.lower().split(":")

    MODS += [
        f"integrations.{origin.strip()}.{dest.strip()}.tasks" for dest in dests.split()
    ]


app = Celery(
    task_acks_late=True,
    broker=os.environ["REDIS_URL"],
    redis_max_connections=int(os.getenv("REDIS_MAX_CONN", 20)),
    include=MODS
    + [
        "signup_processors." + crm.strip()
        for crm in filter(None, os.environ.get("CRMS", "").split(","))
    ],
)


@worker_process_init.connect
def open_sessions(*args, **kwargs):
    app.db = Session()
    app.client = Client()


@worker_process_shutdown.connect
def close_sessions(*args, **kwargs):
    app.db.close()
    app.client.close()
