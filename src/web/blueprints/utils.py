from os import environ

from quart import current_app


async def turnstile_validate(type, token):
    try:
        respData = await (
            await current_app.client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": environ["TURNSTILE_SECRET"],
                    "response": token,
                    # "remoteip": request.remote_addr,
                },
            )
        ).json()

        if (
            not respData["success"]
            or respData["action"] != environ[f"TURNSTILE_{type}_ACTION"]
        ):
            current_app.logger.error(
                "Turnstile Error Codes: " + ", ".join(respData.get("error-codes", []))
            )

            return (
                ""
                if "internal-error" in respData["error-codes"]
                else "Not a bot? Please let us know."
            ), 400

    except Exception:
        current_app.logger.exception("Turnstile Exception")
        pass
