from os import environ

from integrations.stripe.utils import CUSTOM_FIELDS
from quart import Blueprint, current_app, render_template, request

from .utils import cache_progress, exchange_rate


bp = Blueprint("forms", __name__, url_prefix="/form", template_folder="templates")


@bp.route("/")
async def show():
    goal = request.args.get("goal")
    params = {
        **request.args,
        "country_code": request.args.get(
            "country_code", current_app.config["COUNTRIES"][0][0]
        ).upper(),
        "currency": request.args.get(
            "currency",
            list(current_app.config["CURRENCIES"])[0],
        )
        .strip()
        .upper(),
        "interval": request.args.get("interval", "once").lower(),
        "custom_fields": {},
        "message_label": request.args.get("message_label")
        or environ.get("MESSAGE_LABEL"),
    }

    for cf in request.args.getlist("custom_field"):
        _k, v = cf.split(":", maxsplit=1)
        k = "fundist_" + _k

        if k in CUSTOM_FIELDS:
            params["custom_fields"][k] = v

    if goal:
        attr, f_str = (
            ("number", f"{{}} {request.args.get('type', environ['TYPE']).title()}s")
            if goal[0].isdigit()
            else ("amount", goal[0] + "{}")
        )

        num = float(goal[1:] if attr == "amount" else goal)
        params["goal"] = f_str.format(
            f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
        )

        if "tag" in request.args:
            try:
                params["progress"] = round(
                    (
                        sum(
                            [
                                getattr(prog, attr)
                                * (
                                    await exchange_rate(
                                        prog.currency, params["currency"]
                                    )
                                    if attr == "amount"
                                    and params["currency"] != prog.currency
                                    else 1
                                )
                                for prog in await cache_progress(request.args["tag"])
                            ]
                        )
                        + float(request.args.get("add", "0").replace(",", ""))
                    )
                    / num
                    * 100
                )
            except Exception:
                del params["goal"]

    return (
        await render_template("forms/content.html", params=params),
        200,
        {"Cache-Control": "max-age=60"},
    )
