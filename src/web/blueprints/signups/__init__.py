# from os import environ

from quart import Blueprint, current_app, request

from ..utils import turnstile_validate


# from quart_cors import cors


# bp = cors(
#     Blueprint("signups", __name__, url_prefix="/signup"),
#     allow_origin={d.strip() for d in environ["DOMAINS"].split()},
# )


bp = Blueprint("signups", __name__, url_prefix="/signup")


@bp.after_request
async def cache_control(resp):
    resp.headers["Cache-Control"] = "no-cache, no-store"
    return resp


@bp.route("/", methods=["POST"])
async def create():
    data = await request.get_json()

    # try:
    #     turnstile_res = await turnstile_validate(
    #         "SIGNUP", data["transaction"].pop("turnstileToken")
    #     )
    # except Exception:
    #     current_app.logger.exception("No Turnstile token?")
    #     raise

    # if turnstile_res is not None:
    #     current_app.logger.error("Turnstile Error: " + turnstile_res[0])
    #     current_app.logger.error("Signup / Petition Error: " + str(data))
    #     return turnstile_res

    for task in current_app.config["SIGNUP_TASKS"]:
        try:
            task.delay(data)
        except Exception:
            current_app.logger.error("Signup / Petition Error: " + str(data))
            current_app.logger.exception("")
            # test a raise response
            raise

    return "", 202
