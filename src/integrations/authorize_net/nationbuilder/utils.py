from resource_translate import Translator, attr


class Person(Translator):
    mapping = {
        "first_name": ("billTo", "firstName"),
        "last_name": ("billTo", "lastName"),
        "email": ("customer", "email"),
        "billing_address": {
            "zip": ("billTo", "zip"),
            "country_code": ("billTo", "country"),
        },
    }


class Donation(Translator):
    constants = {"currency": "CAD"}
    mapping = {
        "tracking_code_slug": ("order", "description"),
        "native_amount": "authAmount",
    }

    @attr
    def succeeded_at(self):
        return self.resource["submitTimeUTC"].rsplit(".")[0] + "-00:00"

    @attr
    def amount_in_cents(self):
        return int(self.resource["authAmount"] * 100)

    @attr
    def payment_type_name(self):
        if "creditCard" in self.resource["payment"]:
            return "Credit Card"

        return "Other"

    @attr
    def check_number(self):
        return "Authorize.net " + self.resource["transId"]
