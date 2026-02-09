from collections import OrderedDict

from integrations.authorize_net.utils import AUTHNET_AUTH


class Transaction:
    def __init__(self, data, from_map):
        self.repr = {
            "createTransactionRequest": OrderedDict(
                merchantAuthentication=AUTHNET_AUTH,
                transactionRequest=OrderedDict(
                    transactionType="authCaptureTransaction",
                    amount=data["transaction"]["amount"].replace(",", ""),
                    payment={
                        "opaqueData": OrderedDict(
                            dataDescriptor=data["payment"]["dataDescriptor"],
                            dataValue=data["payment"]["dataValue"],
                        )
                    },
                    order=OrderedDict(invoiceNumber="Fundist"),
                    customer={"email": data["user"]["email"]},
                    billTo=OrderedDict(
                        firstName=data["user"]["first_name"],
                        lastName=data["user"]["last_name"],
                        zip=data["user"]["postal_code"],
                        country=data["user"]["country_code"],
                    ),
                    transactionSettings=[
                        {
                            "setting": OrderedDict(
                                settingName="emailCustomer",
                                settingValue=True,
                            )
                        }
                    ],
                ),
            )
        }

        if "tag" in data["transaction"]:
            self.repr["createTransactionRequest"]["transactionRequest"]["order"][
                "description"
            ] = data["transaction"]["tag"]
