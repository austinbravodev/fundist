from collections import OrderedDict
from importlib import import_module
from os import environ, scandir

from aiohttp import ClientSession, ClientTimeout
from aiohttp_client_cache import CachedSession, SQLiteBackend
from babel import Locale
from quart import Quart, send_from_directory

from .blueprints.events import bp as bp_evt
from .blueprints.forms import bp as bp_form
from .blueprints.forms_campaign import bp as bp_form_campaign
from .blueprints.forms_signup import bp as bp_form_signup
from .blueprints.logs import bp as bp_log
from .blueprints.signups import bp as bp_signup
from .blueprints.transactions import bp as bp_trx


CC = [cc.strip().upper() for cc in environ["COUNTRY_CODES"].split(",")]
LOCALE = Locale("en", CC[0])
TIMEOUT = ClientTimeout(total=30)


app = Quart(__name__)

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config |= {
    "ACTION": environ["ACTION"],
    "ACTION_SIGNUP": environ["ACTION_SIGNUP"],
    "ACTION_CAMPAIGN": environ["ACTION_CAMPAIGN"],
    "ADDRESS": environ.get("ADDRESS"),
    "CACHE": {
        "PROGRESS": ({}, int(environ.get("PROGRESS_CACHE_LENGTH", 60))),
    },
    "COUNTRIES": [(cc, LOCALE.territories[cc]) for cc in CC],
    "CURRENCIES": OrderedDict(
        (curr, LOCALE.currency_symbols[curr][-1])
        for curr in (curr.strip().upper() for curr in environ["CURRENCIES"].split(","))
    ),
    "DEDUCTIBLE": environ.get("DEDUCTIBLE"),
    "DOMAINS": " ".join(d.strip() for d in environ["DOMAINS"].split()),
    "FALLBACK_URL": environ.get("FALLBACK_URL"),
    "FALLBACK_URL_SIGNUP": environ.get("FALLBACK_URL_SIGNUP"),
    "LEGAL_NAME": environ["LEGAL_NAME"],
    "NAME": environ["NAME"],
    "ORGANIZATION_NAME": environ.get("ORGANIZATION_NAME", "").lower(),
    "TERMS": environ.get("TERMS"),
    "PROCS": {},
    "SCRIPTS": environ.get("SCRIPTS", "").split(),
    "SIGNUP_TASKS": [
        import_module("signup_processors." + crm.strip()).create_signup
        for crm in filter(None, environ.get("CRMS", "").split(","))
    ],
    "STRIPE_PUBLIC_KEY": environ.get("STRIPE_PUBLIC_KEY", ""),
    "SUPPORT_EMAIL": environ["SUPPORT_EMAIL"],
    "TURNSTILE_SITE_KEY": environ["TURNSTILE_SITE_KEY"],
    "TWITTER": environ.get("TWITTER"),
    "TYPE": environ["TYPE"],
}


for ev in environ:
    if ev.endswith("_PROCESSOR"):
        meth, name = ev[:-10].lower(), environ[ev].lower()
        app.config["PROCS"][meth] = name, {}

        with scandir("processors/" + name) as it:
            for entry in it:
                if entry.is_dir() and not entry.name.startswith((".", "__")):
                    mod = import_module(entry.path.replace("/", "."))

                    if hasattr(mod, "handle"):
                        app.config["PROCS"][meth][1][entry.name] = [
                            *getattr(mod, "PREREQS", ()),
                            mod,
                        ]


for plats in filter(None, environ.get("INTEGRATIONS", "").split(",")):
    origin, dests = plats.lower().split(":")
    origin = origin.strip()

    for dest in dests.split():
        bp_evt.route(
            f"/{origin}/{dest}", methods=["POST"], endpoint=f"{origin}_{dest}"
        )(import_module(f"integrations.{origin}.{dest}").event)


app.register_blueprint(bp_form)
app.register_blueprint(bp_trx)
app.register_blueprint(bp_evt)
app.register_blueprint(bp_form_signup)
app.register_blueprint(bp_form_campaign)
app.register_blueprint(bp_signup)
app.register_blueprint(bp_log)


@app.before_serving
async def open_sessions():
    app.client = ClientSession(timeout=TIMEOUT)


@app.while_serving
async def manage_sessions():
    async with CachedSession(
        cache=SQLiteBackend(expire_after=-1), timeout=TIMEOUT
    ) as client:
        app.cached_client = client
        yield


@app.after_serving
async def close_sessions():
    await app.client.close()


@app.route("/.well-known/apple-developer-merchantid-domain-association")
async def apple_pay_verification():
    return await send_from_directory(
        app.static_folder, "apple-developer-merchantid-domain-association"
    )
