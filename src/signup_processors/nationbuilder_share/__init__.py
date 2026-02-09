from os import environ

from integrations.utils import nationbuilder_request, nationbuilder_task

from .utils import Person


NB_URL = f"https://{environ['NATIONBUILDER_SHARE_ID']}.nationbuilder.com/api/v1/"
NB_PARAMS = {"access_token": environ["NATIONBUILDER_SHARE_KEY"]}


@nationbuilder_task
def create_signup(self, data):
    if "fundist_share" in data["transaction"]:
        """state = (
            self.app.client.get(
                "https://api.emailable.com/v1/verify",
                params={
                    "email": data["user"]["email"],
                    "timeout": 30,
                    "api_key": environ["EMAILABLE_SHARE_API_KEY"],
                },
            )
            .json()
            .get("state")
        )

        if state in {"risky", "undeliverable"}:
            return
        elif state != "deliverable":
            raise Exception"""

        create_person.delay(data)


@nationbuilder_task
@nationbuilder_request(NB_URL, NB_PARAMS)
def create_person(self, data):
    person_id = yield Person(data, from_map=True).repr

    if "fundist_petition_id_share" in data["transaction"]:
        create_signature.delay(
            data["transaction"]["fundist_petition_id_share"],
            person_id,
            data["transaction"].get("message", ""),
        )


@nationbuilder_task
def create_signature(self, petition_id, person_id, comment):
    self.app.client.post(
        NB_URL
        + f"sites/{environ['NB_SHARE_SITE_SLUG']}/pages/petitions/{petition_id}/signatures",
        params=NB_PARAMS,
        json={
            "signature": {
                "person_id": person_id,
                "comment": comment,
            }
        },
    )
