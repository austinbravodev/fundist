# from os import environ

from processors.utils import ProcessorError
from quart import Blueprint, current_app, request

from ..utils import turnstile_validate


# from quart_cors import cors


# bp = cors(
#     Blueprint("transactions", __name__, url_prefix="/transaction"),
#     allow_origin={d.strip() for d in environ["DOMAINS"].split()},
# )


bp = Blueprint("transactions", __name__, url_prefix="/transaction")


@bp.after_request
async def cache_control(resp):
    resp.headers["Cache-Control"] = "no-cache, no-store"
    return resp


@bp.route("/<method>", methods=["POST"])
async def create(method):
    data = await request.get_json()

    # if "stripe_wallet" not in data["transaction"]:
    #     try:
    #         turnstile_res = await turnstile_validate(
    #             "DONATION", data["transaction"].pop("turnstileToken")
    #         )
    #     except Exception:
    #         current_app.logger.exception("No Turnstile token?")
    #         raise

    #     if turnstile_res is not None:
    #         current_app.logger.error("Turnstile Error: " + turnstile_res[0])
    #         current_app.logger.error("Donation Error: " + str(data))
    #         return turnstile_res

    res = {}

    for mod in current_app.config["PROCS"][method][1][
        "recurring" if "interval" in data["transaction"] else "transaction"
    ]:
        try:
            res = await mod.handle(
                await current_app.client.post(
                    **{
                        param: (
                            val(data, from_map=True).repr | res
                            if param in {"data", "json"}
                            else val
                        )
                        for param, val in mod.PARAMS.items()
                    }
                )
            )
        except Exception as exc:
            msg = str(exc) if isinstance(exc, ProcessorError) else ""
            current_app.logger.error("Donation Error: " + str(data))
            current_app.logger.exception(msg)
            return msg, 400

    return res
