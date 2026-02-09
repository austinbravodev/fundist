from functools import partial, wraps

from requests import Session


def lock(f_or_timeout):
    def dec(f, timeout=30):
        @wraps(f)
        def dec_f(self, *args, **kwargs):
            with self.app.connection_or_acquire() as conn:
                with conn.default_channel.client.lock(
                    f.__name__, timeout, blocking_timeout=5
                ):
                    return f(self, *args, **kwargs)

        return dec_f

    return (
        dec(f_or_timeout)
        if callable(f_or_timeout)
        else partial(dec, timeout=f_or_timeout)
    )


class Client(Session):
    def __init__(self, timeout=30, raise_for_status=True):
        super().__init__()
        self.request = partial(self.request, timeout=timeout)

        if raise_for_status:
            self.hooks["response"].append(
                lambda resp, *args, **kwargs: resp.raise_for_status()
            )
