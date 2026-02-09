/* global Stripe, ApplePaySession, fdMailingSlug, fdMsgRemaining, $fdMsg, fdEach, fdIsOrg, $fdIsOrg, fdName, fdStripePubkey, fdData, fdMessages, fdSuccess, fdUrl, $fdAmt, $fdCurr, fdNoSupport, fdInt, $fdInt */

if (ApplePaySession && "Stripe" in window && "fetch" in window) {
  const $fdTransFields = document.querySelectorAll(
    '[data-fd-field="transaction"]'
  );

  const initAp = function (func) {
    document.querySelector("#apBtn").addEventListener("click", () => {
      let valid = true;

      fdEach($fdTransFields, ($field) => {
        if (!$field.validity.valid) {
          valid = false;
          $field.reportValidity();
          return true;
        }
      });

      if (valid) func();
    });
    document.querySelector("#wallet").classList.remove("d-none");
  };

  Stripe.setPublishableKey(fdStripePubkey);

  try {
    var isTop = window.self === window.top;
  } catch (exc) {
    isTop = false;
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (isTop) {
      Stripe.applePay.checkAvailability(function (avail) {
        if (avail) {
          const fdUrlParams = new URLSearchParams(window.location.search);

          initAp(() => {
            const chargeData = { user: {} };

            fdData(chargeData, $fdTransFields);

            const apMailingSlug =
              fdMailingSlug || fdUrlParams.get("mailing_slug");

            if (apMailingSlug) {
              const mailingSlug = apMailingSlug.split(" ");

              chargeData.transaction[mailingSlug[0]] = mailingSlug[1];
            }

            let processing = false,
              session = Stripe.applePay.buildSession(
                {
                  countryCode: "CA",
                  currencyCode: chargeData.transaction.currency,
                  merchantCapabilities: ["supports3DS"],
                  supportedNetworks: ["visa", "masterCard", "amex", "discover"],
                  requiredBillingContactFields: ["postalAddress"],
                  requiredShippingContactFields: ["email"],
                  total: {
                    label: fdName + (fdInt ? " " + fdInt : ""),
                    amount: chargeData.transaction.amount.replace(/,/g, ""),
                  },
                },
                async (res, comp) => {
                  let resp,
                    status = ApplePaySession.STATUS_FAILURE;

                  chargeData.payment = res.token.id;
                  chargeData.user.email = res.shippingContact.emailAddress;

                  let respProm = fetch(fdUrl + "card", {
                    method: "POST",
                    cache: "no-store",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify(chargeData),
                  });

                  processing = true;

                  try {
                    resp = await respProm;
                  } catch (exc) {
                    processing = false;
                    fdMessages();
                  }

                  if (resp) {
                    if ([201, 202].includes(resp.status)) {
                      fdSuccess(resp.status);
                      processing = false;

                      if (res.token.card) {
                        const $apCard = document.querySelector("#apCard");
                        $apCard.querySelector("input").value =
                          (res.token.card.brand
                            ? res.token.card.brand + " "
                            : "") +
                          "****" +
                          (res.token.card.last4 || "");
                        $apCard.classList.remove("d-none");
                      }

                      status = ApplePaySession.STATUS_SUCCESS;
                    } else {
                      processing = false;

                      try {
                        fdMessages(await resp.text());
                      } catch (exc) {
                        fdMessages();
                      }
                    }
                  }

                  comp(status);
                },
                (err) => {
                  fdMessages(err.message);
                }
              );

            session.addEventListener("paymentauthorized", (ev) => {
              chargeData.user.first_name = ev.payment.billingContact.givenName;
              chargeData.user.last_name = ev.payment.billingContact.familyName;
            });

            session.oncancel = () => {
              if (processing) {
                fdMessages(
                  "Your Apple Pay donation is processing - please check your email for receipt.",
                  "warning"
                );
              }
            };

            session.begin();
          });

          if ($fdIsOrg) {
            const orgName = fdUrlParams.get("organization_name");

            if (orgName) {
              document.querySelector("#organization_name").value = orgName;
              $fdIsOrg.checked = true;
              fdIsOrg();
            }
          }

          if ($fdMsg) {
            const msg = fdUrlParams.get("message");

            if (msg) {
              $fdMsg.value = msg;
              fdMsgRemaining();
            }
          }
        }
      });
    } else {
      initAp(() => {
        if ($fdAmt.value) {
          const url = new URL(window.location.href);

          url.searchParams.delete("iframe");
          url.searchParams.set("amount", $fdAmt.value);
          url.searchParams.set("currency", $fdCurr.value);
          url.searchParams.set("interval", $fdInt.value);

          if ($fdIsOrg && $fdIsOrg.checked) {
            const orgName = document.querySelector("#organization_name").value;

            if (orgName) {
              url.searchParams.set("organization_name", orgName);
            }
          }

          if ($fdMsg) {
            const msg = $fdMsg.value;

            if (msg) url.searchParams.set("message", msg);
          }

          if (fdMailingSlug) {
            url.searchParams.set("mailing_slug", fdMailingSlug);
          }

          const urlStr = url.toString();

          try {
            window.top.location.href = urlStr;
          } catch (exc) {
            try {
              window.top.location = urlStr;
            } catch (exc) {
              fdMessages(fdNoSupport);
            }
          }
        } else {
          $fdAmt.reportValidity();
        }
      });
    }
  });
}
