from os import environ

from integrations.stripe.utils import CUSTOM_FIELDS
from resource_translate import Translator

from ...utils import ProcessorError, get_json


class Subscription(Translator):
    constants = {
        "payment_behavior": "error_if_incomplete",
        "items[0][price_data][product]": environ["STRIPE_PRODUCT_ID"],
        # "proration_behavior": "none",
    }
    mapping = {
        "items[0][price_data][recurring][interval]": ("transaction", "interval"),
        "metadata[first_name]": ("user", "first_name"),
        "metadata[last_name]": ("user", "last_name"),
        "metadata[email]": ("user", "email"),
        "metadata[tag]": ("transaction", "tag"),
        "metadata[fundist_organization_name]": ("transaction", "organization_name"),
        "metadata[fundist_message]": ("transaction", "message"),
        "metadata[mailing_slug]": ("transaction", "mailing_slug"),
        "metadata[mailing_slug_share]": ("transaction", "mailing_slug_share"),
        "metadata[stripe_wallet]": ("transaction", "stripe_wallet"),
        **{f"metadata[{field}]": ("transaction", field) for field in CUSTOM_FIELDS},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.repr["items[0][price_data][currency]"] = self.resource["transaction"][
            "currency"
        ].lower()

        self.repr["items[0][price_data][unit_amount]"] = int(
            float(self.resource["transaction"]["amount"].replace(",", "")) * 100
        )


@get_json
def customer_handle(res):
    if res.get("object") == "customer":
        return {"customer": res["id"]}

    raise ProcessorError(res["error"]["message"])
