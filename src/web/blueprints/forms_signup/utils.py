from os import environ


CUSTOM_FIELDS = [
    "fundist_" + f
    for f in (_f.strip() for _f in environ.get("CUSTOM_FIELDS_SIGNUP", "").split(","))
    if f
]
