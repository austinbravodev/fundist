import time
from functools import wraps
from hashlib import sha256
from hmac import compare_digest, new
from os import environ

from quart import current_app, request


AUTH = environ["STRIPE_KEY"], ""
CHARGE_URL = "https://api.stripe.com/v1/charges/"

CUSTOM_FIELDS = [
    "fundist_" + f
    for f in (_f.strip() for _f in environ.get("CUSTOM_FIELDS", "").split(","))
    if f
]


def validate(secret):
    def dec(f):
        @wraps(f)
        async def dec_f(scheme="v1", tolerance=300):
            sigs = set()

            try:
                for n, v in (
                    nv.split("=")
                    for nv in request.headers["Stripe-Signature"].split(",")
                ):
                    if n == "t":
                        if int(v) < time.time() - tolerance:
                            raise Exception

                        exp_sig = new(
                            secret.encode(),
                            f"{v}.{await request.get_data(as_text=True)}".encode(),
                            sha256,
                        ).hexdigest()
                    elif n == scheme:
                        sigs.add(v)

                if any(compare_digest(exp_sig, sig) for sig in sigs):
                    resource = (await request.get_json())["data"]["object"]

                    if resource["livemode"]:
                        f(resource)

                    return ""

            except Exception:
                current_app.logger.exception("")

            return "", 400

        return dec_f

    return dec


def get_charge(f):
    @wraps(f)
    def dec_f(self, charge_id):
        charge = self.app.client.get(
            CHARGE_URL + charge_id,
            auth=AUTH,
            data={"expand[]": "balance_transaction"},
        ).json()

        if "stripe_wallet" in charge["metadata"] or {
            "first_name",
            "last_name",
        }.issubset(charge["metadata"]):
            return f(self, charge)

    return dec_f
