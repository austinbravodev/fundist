from os import environ

from celery import chain
from integrations.stripe.database.tasks import update_progress
from integrations.stripe.nationbuilder.tasks import (create_donation,
                                                     create_person_add)
from integrations.stripe.sendgrid.tasks import create_receipt

from ...utils import task
from ..utils import AUTH, CHARGE_URL, CUSTOM_FIELDS


if "fundist_share" in CUSTOM_FIELDS:
    from integrations.stripe.nationbuilder_share.tasks import (
        create_person_add as create_person_add_share,
        create_donation as create_donation_share,
    )


@task
def update_charge(self, invoice_id):
    inv = self.app.client.get(
        "https://api.stripe.com/v1/invoices/" + invoice_id,
        auth=AUTH,
        data={"expand[]": "charge"},
    ).json()

    if "interval" not in inv["charge"]["metadata"]:
        for item in inv["lines"]["data"]:
            if item["price"]["product"] == environ["STRIPE_PRODUCT_ID"]:
                data = {
                    **{
                        f"metadata[{field}]": item["metadata"][field]
                        for field in CUSTOM_FIELDS
                        if field in item["metadata"]
                    },
                    "metadata[email]": item["metadata"]["email"],
                    "metadata[interval]": item["price"]["recurring"][
                        "interval"
                    ].capitalize(),
                }

                if "first_name" in item["metadata"]:
                    data["metadata[first_name]"] = item["metadata"]["first_name"]

                if "last_name" in item["metadata"]:
                    data["metadata[last_name]"] = item["metadata"]["last_name"]

                if "tag" in item["metadata"]:
                    data["description"] = item["metadata"]["tag"]

                if "fundist_organization_name" in item["metadata"]:
                    data["metadata[fundist_organization_name]"] = item["metadata"][
                        "fundist_organization_name"
                    ]

                if "fundist_message" in item["metadata"]:
                    data["metadata[fundist_message]"] = item["metadata"][
                        "fundist_message"
                    ]

                if "mailing_slug" in item["metadata"]:
                    data["metadata[mailing_slug]"] = item["metadata"]["mailing_slug"]

                if "mailing_slug_share" in item["metadata"]:
                    data["metadata[mailing_slug_share]"] = item["metadata"][
                        "mailing_slug_share"
                    ]

                if "stripe_wallet" in item["metadata"]:
                    data["metadata[stripe_wallet]"] = item["metadata"]["stripe_wallet"]

                self.app.client.post(
                    CHARGE_URL + inv["charge"]["id"], auth=AUTH, data=data
                )

                create_receipt.delay(inv["charge"]["id"])

                if "description" in data:
                    update_progress.delay(inv["charge"]["id"])

                chain(
                    [
                        create_person_add.si(inv["charge"]["id"]),
                        create_donation.si(inv["charge"]["id"]),
                    ]
                ).delay()

                if "fundist_share" in item["metadata"]:
                    chain(
                        [
                            create_person_add_share.si(inv["charge"]["id"]),
                            create_donation_share.si(inv["charge"]["id"]),
                        ]
                    ).delay()

                break
