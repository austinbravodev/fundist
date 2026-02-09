from datetime import datetime

from resource_translate import Translator, attr


class Person(Translator):
    mapping = {
        "first_name": ("metadata", "first_name"),
        "last_name": ("metadata", "last_name"),
        "employer": ("metadata", "fundist_organization_name"),
    }

    @attr
    def email(self):
        return self.resource.get("receipt_email") or self.resource["metadata"]["email"]

    @attr
    def tags(self):
        if "fundist_tags_share" in self.resource["metadata"]:
            ts = []

            for _t in self.resource["metadata"]["fundist_tags_share"].split(","):
                t = _t.strip()

                if t:
                    ts.append(t)

            if ts:
                return ts


class Donation(Translator):
    mapping = {
        "amount_in_cents": ("balance_transaction", "amount"),
        "tracking_code_slug": "description",
        "interval": ("metadata", "interval"),
        "fundist_message": ("metadata", "fundist_message"),
        "mailing_slug": ("metadata", "mailing_slug_share"),
        "billing_address": {
            "address1": ("billing_details", "address", "line1"),
            "address2": ("billing_details", "address", "line2"),
            "city": ("billing_details", "address", "city"),
            "state": ("billing_details", "address", "state"),
            "zip": ("billing_details", "address", "postal_code"),
            "country_code": ("billing_details", "address", "country"),
        },
    }

    @attr
    def donor_id(self):
        return self.resource["metadata"]["nationbuilder_share_person"]

    @attr
    def succeeded_at(self):
        return (
            datetime.utcfromtimestamp(self.resource["created"]).isoformat() + "-00:00"
        )

    @attr
    def payment_type_name(self):
        if self.resource["metadata"].get("stripe_wallet") == "link":
            return "ActBlue"

        try:
            wallet_type = self.resource["payment_method_details"][
                self.resource["payment_method_details"]["type"]
            ]["wallet"]["type"]

            if wallet_type == "apple_pay":
                return "Apple Pay"
            elif wallet_type == "google_pay":
                return "Google Pay"

        except Exception:
            pass

        if self.resource["payment_method_details"]["type"] == "card":
            return "Credit Card"

        return "Other"

    @attr
    def check_number(self):
        return "Stripe " + self.resource["id"]

    @attr
    def currency(self):
        return self.resource["currency"].upper()

    @attr
    def native_amount(self):
        return self.resource["amount"] / 100

    @attr
    def corporate_contribution(self):
        if "fundist_organization_name" in self.resource["metadata"]:
            return True
