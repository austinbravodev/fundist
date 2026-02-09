from ...utils import nationbuilder_request, nationbuilder_task
from ..utils import get_transaction
from .utils import Donation, Person


@nationbuilder_task
@get_transaction
@nationbuilder_request
def create_person(self, trx):
    create_donation.delay(trx["transId"], (yield Person(trx, from_map=True).repr))


@nationbuilder_task
@get_transaction
@nationbuilder_request
def create_donation(self, trx, person_id):
    yield Donation(trx, donor_id=person_id, from_map=True).repr
