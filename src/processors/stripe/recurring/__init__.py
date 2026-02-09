import processors.stripe.user as user

from ...utils import ProcessorError, get_json
from ..utils import _PARAMS, URL
from .utils import Subscription, customer_handle


user.handle = customer_handle

PREREQS = (user,)
PARAMS = _PARAMS | {"url": URL + "subscriptions", "data": Subscription}


@get_json
def handle(res):
    if res.get("object") == "subscription":
        if res["status"] == "active":
            return "", 201

        # if res["status"] == "pending":
        # return "", 202

    raise ProcessorError(res["error"]["message"])
