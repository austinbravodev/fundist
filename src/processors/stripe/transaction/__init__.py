from ...utils import ProcessorError, get_json
from ..utils import _PARAMS, URL
from .utils import Charge


PARAMS = _PARAMS | {"url": URL + "charges", "data": Charge}


@get_json
def handle(res):
    if res.get("object") == "charge":
        if res["status"] == "succeeded":
            return "", 201

        if res["status"] == "pending":
            return "", 202

    raise ProcessorError(res.get("failure_message", res["error"]["message"]))
