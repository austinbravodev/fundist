from functools import wraps

from database.models import Progress
from worker import app


TASK_OPTS = {
    "bind": True,
    "time_limit": 30,
    "autoretry_for": (Exception,),
    "max_retries": 10,
    "retry_backoff": 60,
    "retry_backoff_max": 30720,
    "retry_jitter": False,
}

NB_REQS = {
    "create_person": ("put", "people/push", "person"),
    "create_person_add": ("put", "people/add", "person"),
    "create_donation": ("post", "donations", "donation"),
    "create_signup": ("put", "people/push", "person"),
}


task = app.task(**TASK_OPTS)
nationbuilder_task = app.task(**TASK_OPTS, rate_limit="25/s")


def _update_progress(f):
    @wraps(f)
    def dec_f(self, trx):
        with self.app.db.begin():
            for tag, curr, amt in f(self, trx):
                prog = self.app.db.query(Progress).get((tag, curr))

                if prog:
                    prog.amount += amt
                    prog.number += 1
                else:
                    self.app.db.add(Progress(tag=tag, currency=curr, amount=amt))

    return dec_f


def nationbuilder_request(url, params):
    def dec(f):
        @wraps(f)
        def dec_f(self, trx, *args):
            gen = f(self, trx, *args)
            meth, endpoint, name = NB_REQS[f.__name__]

            try:
                gen.send(
                    getattr(self.app.client, meth)(
                        url + endpoint, json={name: next(gen)}, params=params
                    ).json()[name]["id"]
                )
            except StopIteration:
                pass

        return dec_f

    return dec
