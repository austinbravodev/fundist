# from os import environ

from quart import Blueprint, current_app, request


# from quart_cors import cors


# bp = cors(
#     Blueprint("logs", __name__, url_prefix="/log"),
#     allow_origin={d.strip() for d in environ["DOMAINS"].split()},
# )


bp = Blueprint("logs", __name__, url_prefix="/log")


@bp.after_request
async def cache_control(resp):
    resp.headers["Cache-Control"] = "no-cache, no-store"
    return resp


@bp.route("/", methods=["POST"])
async def create():
    for error in (await request.get_json())["errors"]:
        current_app.logger.error(f'Client error: {error["type"]} - {error["message"]}')

    return "", 201
