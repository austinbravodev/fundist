from os import environ

from integrations.stripe.utils import CUSTOM_FIELDS
from resource_translate import Translator, attr


class Charge(Translator):
    mapping = {
        "metadata[first_name]": ("user", "first_name"),
        "metadata[last_name]": ("user", "last_name"),
        "description": ("transaction", "tag"),
        "metadata[email]": ("user", "email"),
        "source": "payment",
        "metadata[fundist_organization_name]": ("transaction", "organization_name"),
        "metadata[fundist_message]": ("transaction", "message"),
        "metadata[mailing_slug]": ("transaction", "mailing_slug"),
        "metadata[mailing_slug_share]": ("transaction", "mailing_slug_share"),
        "metadata[stripe_wallet]": ("transaction", "stripe_wallet"),
        **{f"metadata[{field}]": ("transaction", field) for field in CUSTOM_FIELDS},
    }

    @attr
    def amount(self):
        return int(float(self.resource["transaction"]["amount"].replace(",", "")) * 100)

    @attr
    def currency(self):
        return self.resource["transaction"]["currency"].lower()

    @attr
    def statement_descriptor_suffix(self):
        # return self.resource["transaction"].get("type", environ["TYPE"]).title()
        return "Fundist Donation"
