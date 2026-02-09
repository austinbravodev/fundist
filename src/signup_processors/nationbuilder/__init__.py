from os import environ

from integrations.utils import nationbuilder_request, nationbuilder_task, task
from worker.utils import lock

from .utils import Person


NB_URL = f"https://{environ['NATIONBUILDER_ID']}.nationbuilder.com/api/v1/"
NB_PARAMS = {"access_token": environ["NATIONBUILDER_KEY"]}


@nationbuilder_task
def create_signup(self, data):
    """state = (
        self.app.client.get(
            "https://api.emailable.com/v1/verify",
            params={
                "email": data["user"]["email"],
                "timeout": 30,
                "api_key": environ["EMAILABLE_API_KEY"],
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

    if "fundist_petition_id" in data["transaction"]:
        create_signature.delay(
            data["transaction"]["fundist_petition_id"],
            person_id,
            data["transaction"].get("message", ""),
            data["transaction"].get("cmsEmbedId", False),
        )


@nationbuilder_task
def create_signature(self, petition_id, person_id, comment, cmsEmbedId):
    resp = self.app.client.post(
        NB_URL
        + f"sites/{environ['NB_SITE_SLUG']}/pages/petitions/{petition_id}/signatures",
        params=NB_PARAMS,
        json={
            "signature": {
                "person_id": person_id,
                "comment": comment,
            }
        },
    )

    if cmsEmbedId and environ.get("KEYSTONE_API_URL"):
        if 200 <= resp.status_code < 300:
            incrementEmbedSubmissions.delay(cmsEmbedId)
        else:
            raise Exception(
                "Signature creation failed - could not update Keystone submissions count."
            )


def hitKeystoneAPI(client, data):
    return client.post(
        environ["KEYSTONE_API_URL"],
        json=data,
        headers={"keystone-authorization": environ["KEYSTONE_API_KEY"]},
    ).json()


@task
@lock
def incrementEmbedSubmissions(self, cmsEmbedId):
    resp = hitKeystoneAPI(
        self.app.client,
        {
            "query": "query Embed($where: EmbedWhereUniqueInput!) {\n  embed(where: $where) {\n    fundistSignupSubmissions\n  }\n}",
            "variables": {"where": {"id": cmsEmbedId}},
        },
    )

    hitKeystoneAPI(
        self.app.client,
        {
            "query": "mutation UpdateEmbed($where: EmbedWhereUniqueInput!, $data: EmbedUpdateInput!) {\n  updateEmbed(where: $where, data: $data) {\n    fundistSignupSubmissions\n  }\n}",
            "variables": {
                "where": {"id": cmsEmbedId},
                "data": {
                    "fundistSignupSubmissions": resp["data"]["embed"][
                        "fundistSignupSubmissions"
                    ]
                    + 1
                },
            },
        },
    )
