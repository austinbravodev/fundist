from quart import Blueprint, render_template, request


bp = Blueprint(
    "forms_campaign", __name__, url_prefix="/form_campaign", template_folder="templates"
)


@bp.route("/")
async def show():
    params = {**request.args}

    return (
        await render_template("forms_campaign/content.html", params=params),
        200,
        {"Cache-Control": "max-age=60"},
    )
