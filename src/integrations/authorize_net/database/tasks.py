from ...utils import _update_progress, task
from ..utils import get_transaction


@task
@get_transaction
@_update_progress
def update_progress(self, trx):
    tag = trx["order"].get("description")

    if tag:
        yield tag, "CAD", trx["authAmount"]
