from ..utils import validate
from .tasks import create_person


@validate
def event(trx_id):
    create_person.delay(trx_id)
