from collections import OrderedDict
from functools import wraps
from hashlib import sha512
from hmac import compare_digest, new
from os import environ

from quart import current_app, request


AUTHNET_URL = "https://api.authorize.net/xml/v1/request.api"
AUTHNET_AUTH = OrderedDict(
    name=environ["AUTHORIZENET_ID"], transactionKey=environ["AUTHORIZENET_KEY"]
)


def validate(f):
    @wraps(f)
    async def dec_f():
        try:
            if compare_digest(
                new(
                    environ["AUTHORIZENET_WEBHOOK_SECRET"].encode(),
                    (await request.get_data(as_text=True)).encode(),
                    sha512,
                )
                .hexdigest()
                .lower(),
                request.headers["X-ANET-Signature"].replace("sha512=", "").lower(),
            ):
                payload = (await request.get_json()).get("payload")

                if payload:
                    f(payload["id"])

                return ""

        except Exception:
            current_app.logger.exception("")

        return "", 400

    return dec_f


def get_transaction(f):
    @wraps(f)
    def dec_f(self, trx_id, *args):
        resp = self.app.client.post(
            AUTHNET_URL,
            json={
                "getTransactionDetailsRequest": OrderedDict(
                    merchantAuthentication=AUTHNET_AUTH, transId=trx_id
                )
            },
        )
        resp.encoding = "utf-8-sig"
        trx = resp.json()["transaction"]

        if (
            "order" in trx
            and trx["order"].get("invoiceNumber") == "Fundist"
            and trx["responseCode"] == 1
        ):
            return f(self, trx, *args)

    return dec_f
