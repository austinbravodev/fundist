from os import environ

from quart import Blueprint, current_app, render_template, request

from .utils import CUSTOM_FIELDS


bp = Blueprint(
    "forms_signup", __name__, url_prefix="/form_signup", template_folder="templates"
)


@bp.route("/")
async def show():
    goal = request.args.get("goal")
    params = {
        **request.args,
        "country_code": request.args.get(
            "country_code", current_app.config["COUNTRIES"][0][0]
        ).upper(),
        "custom_fields": {},
        "message_label": request.args.get("message_label")
        or environ.get("MESSAGE_LABEL_SIGNUP"),
        "tag_checkboxes": [
            tuple(t.split(";")) for t in request.args.getlist("tag_checkboxes")
        ],
    }

    for cf in request.args.getlist("custom_field"):
        _k, v = cf.split(":", maxsplit=1)
        k = "fundist_" + _k

        if k in CUSTOM_FIELDS:
            params["custom_fields"][k] = v

    if goal:
        f_str = f"{{}} {request.args.get('type', environ['TYPE']).title()}s"

        num = float(goal)
        params["goal"] = f_str.format(
            f"{int(num):,}" if num.is_integer() else f"{num:,.2f}"
        )

        params["progress"] = round(
            (
                float(request.args.get("signatures", "0").replace(",", ""))
                + float(request.args.get("add", "0").replace(",", ""))
            )
            / num
            * 100
        )

    return (
        await render_template("forms_signup/content.html", params=params),
        200,
        {"Cache-Control": "max-age=60"},
    )
