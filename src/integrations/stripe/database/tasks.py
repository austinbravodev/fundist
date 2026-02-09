from worker.utils import lock

from ...utils import _update_progress, task
from ..utils import AUTH, CHARGE_URL, get_charge


@task
@lock
@get_charge
@_update_progress
def update_progress(self, charge):
    yield charge["description"], charge["currency"].upper(), charge["amount"] / 100

    try:
        self.app.client.post(
            CHARGE_URL + charge["id"], auth=AUTH, data={"metadata[database]": 1}
        )
    except Exception:
        self.app.db.rollback()
        raise
