from functools import partial, wraps


class ProcessorError(Exception):
    pass


def get_json(f_or_encoding):
    def dec(f, encoding=None):
        @wraps(f)
        async def dec_f(resp):
            return f(await resp.json(encoding=encoding))

        return dec_f

    return (
        dec(f_or_encoding)
        if callable(f_or_encoding)
        else partial(dec, encoding=f_or_encoding)
    )
