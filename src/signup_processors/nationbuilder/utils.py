from resource_translate import Translator, attr


class Person(Translator):
    mapping = {
        "first_name": ("user", "first_name"),
        "last_name": ("user", "last_name"),
        "email": ("user", "email"),
        "home_address": {
            "address1": ("user", "address"),
            "address2": ("user", "unit"),
            "city": ("user", "city"),
            "state": ("user", "province"),
            "zip": ("user", "postal_code"),
            "country_code": ("user", "country_code"),
        },
    }

    @attr
    def tags(self):
        if "fundist_tags" in self.resource["transaction"]:
            ts = set()

            for _t in self.resource["transaction"]["fundist_tags"].split(","):
                t = _t.strip()

                if t:
                    ts.add(t)

            if ts:
                return list(ts)
