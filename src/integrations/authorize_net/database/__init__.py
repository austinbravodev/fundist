from ..utils import validate
from .tasks import update_progress


@validate
def event(trx_id):
    update_progress.delay(trx_id)
