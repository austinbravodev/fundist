from integrations.authorize_net.utils import AUTHNET_URL

from ...utils import ProcessorError, get_json
from .utils import Transaction


PARAMS = {
    "url": AUTHNET_URL,
    "json": Transaction,
}


@get_json("utf-8-sig")
def handle(res):
    if "transactionResponse" in res:
        code = res["transactionResponse"].get("responseCode")

        if code == "1":
            return "", 201
        elif code == "2":
            return "", 202
        elif "errors" in res["transactionResponse"]:
            err = res["transactionResponse"]["errors"][0]["errorText"]
        elif "messages" in res["transactionResponse"]:
            err = res["transactionResponse"]["messages"][0]["description"]

    try:
        err
    except Exception:
        if res["messages"]["resultCode"] == "Ok":
            err = res["messages"]["message"][0]["text"]

    raise ProcessorError(err)
