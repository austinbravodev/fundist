from datetime import datetime
from os import environ

from babel import Locale

from ...utils import task
from ..utils import AUTH, CHARGE_URL, get_charge


LOCALE = Locale("en", environ["COUNTRY_CODES"].split(",")[0].strip().upper())

CONTENT = f"""
<p><img src="{environ["LOGO"]}" width="225" /></p>
<p>{{name}}{environ["RECEIPTS_MESSAGE"]}</p>
<p>----------------</p>
<p><strong>Amount</strong><br>{{amt}} {{curr}}</p>
<p><strong>Date</strong><br>{{date}}</p>
<p><strong>Method</strong><br>{{meth}}</p>{{tag}}
"""


@task
@get_charge
def create_receipt(self, charge):
    card, to, bcc, curr = (
        charge["payment_method_details"].get("card"),
        {
            "to": [{"email": charge["metadata"]["email"]}],
        },
        environ.get("RECEIPTS_BCC"),
        charge["currency"].upper(),
    )

    first_name = charge["metadata"].get("first_name")
    last_name = charge["metadata"].get("last_name")

    if first_name and last_name:
        to["to"][0]["name"] = first_name + " " + last_name
    else:
        billing_details_name = charge.get("billing_details", {}).get("name")

        if billing_details_name:
            to["to"][0]["name"] = billing_details_name

    if card:
        meth = [card.get("brand", "").title()]
        last = card.get("last4")

        if last:
            meth.append("****" + last)

        try:
            meth.append(f'({card["wallet"]["type"].replace("_", " ").title()})')
        except Exception:
            pass

    if bcc and bcc != charge["metadata"]["email"]:
        to["bcc"] = [{"email": bcc}]

    self.app.client.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": "Bearer " + environ["SENDGRID_API_KEY"]},
        json={
            "personalizations": [to],
            "from": {
                k: v.strip()
                for k, v in zip(["email", "name"], environ["RECEIPTS_EMAIL"].split(":"))
            },
            "subject": environ["NAME"]
            + (
                " "
                + charge["metadata"]["interval"]
                .replace("Month", "Monthly")
                .replace("Year", "Annual")
                if "interval" in charge["metadata"]
                else ""
            )
            + " "
            + environ["TYPE"].title()
            + " Receipt",
            "content": [
                {
                    "type": "text/html",
                    "value": CONTENT.format(
                        name=first_name + " - " if first_name else "",
                        amt=LOCALE.currency_symbols[curr][-1]
                        + "{:,.2f}".format(charge["amount"] / 100),
                        curr=curr,
                        date=datetime.fromtimestamp(charge["created"])
                        .astimezone()
                        .strftime("%-d %b %Y %-I:%M%p %Z"),
                        meth=" ".join(comp for comp in meth if comp),
                        tag="<p><strong>Campaign</strong><br>"
                        + charge["description"]
                        + "</p>"
                        if charge["description"]
                        else "",
                    ),
                }
            ],
            "mail_settings": {"bypass_list_management": {"enable": True}},
        },
    )

    self.app.client.post(
        CHARGE_URL + charge["id"],
        auth=AUTH,
        data={"metadata[fundist_receipt]": 1},
    )
