from ..utils import _PARAMS, URL
from .utils import Customer


PARAMS = _PARAMS | {"url": URL + "customers", "data": Customer}
