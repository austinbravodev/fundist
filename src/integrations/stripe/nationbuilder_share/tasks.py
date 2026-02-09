from os import environ

from ...utils import nationbuilder_request, nationbuilder_task
from ..utils import AUTH, CHARGE_URL, get_charge
from .utils import Donation, Person


NB_URL = f"https://{environ['NATIONBUILDER_SHARE_ID']}.nationbuilder.com/api/v1/"
NB_PARAMS = {"access_token": environ["NATIONBUILDER_SHARE_KEY"]}


@nationbuilder_task
@get_charge
@nationbuilder_request(NB_URL, NB_PARAMS)
def create_person(self, charge):
    self.app.client.post(
        CHARGE_URL + charge["id"],
        auth=AUTH,
        data={
            "metadata[nationbuilder_share_person]": (
                yield Person(charge, from_map=True).repr
            )
        },
    )


@nationbuilder_task
@get_charge
@nationbuilder_request(NB_URL, NB_PARAMS)
def create_person_add(self, charge):
    self.app.client.post(
        CHARGE_URL + charge["id"],
        auth=AUTH,
        data={
            "metadata[nationbuilder_share_person]": (
                yield Person(charge, from_map=True).repr
            )
        },
    )


@nationbuilder_task
@get_charge
@nationbuilder_request(NB_URL, NB_PARAMS)
def create_donation(self, charge):
    donation_id = yield Donation(charge, from_map=True).repr

    try:
        self.app.client.post(
            CHARGE_URL + charge["id"],
            auth=AUTH,
            data={"metadata[nationbuilder_share_donation]": donation_id},
        )
    except Exception:
        self.app.client.delete(f"{NB_URL}donations/{donation_id}", params=NB_PARAMS)
        raise
