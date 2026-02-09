/* global
  fdSuccess,
  fdUrl,
  fdData,
  fdMailingSlug,
  Stripe,
  fdStripePubkey,
  $fdCurr,
  fdName,
  fdInt,
  $fdAmt,
  fdMessages,
  fdEach,
  ApplePaySession,
  fdNoSupport,
  $fdInt,
  $fdIsOrg,
  $fdMsg
*/

document.addEventListener("DOMContentLoaded", async () => {
  if ("Stripe" in window) {
    let isStripeApplePay;

    const stripe = Stripe(fdStripePubkey, { apiVersion: "2022-11-15" });
    const paymentRequest = stripe.paymentRequest({
      country: "CA",
      currency: $fdCurr.value.toLowerCase(),
      total: { label: "Stub", amount: 100 },
      requestPayerName: true,
      requestPayerEmail: true,
      //disableWallets: ["link"],
    });

    const prCanMakePayment = await paymentRequest.canMakePayment();

    if (prCanMakePayment) {
      let processing = false;
      const $fdTransFields = document.querySelectorAll(
        '[data-fd-field="transaction"]'
      );

      paymentRequest.on("cancel", async () => {
        if (processing) {
          fdMessages(
            "Your donation is processing - please check your email for receipt.",
            "warning"
          );
        }
      });

      paymentRequest.on("token", async (evt) => {
        const data = {
          payment: evt.token.id,
          transaction: { stripe_wallet: evt.walletName },
        };

        fdData(data, $fdTransFields);
        data.user = { email: evt.payerEmail };

        if (fdMailingSlug) {
          const mailingSlug = fdMailingSlug.split(" ");

          data.transaction[mailingSlug[0]] = mailingSlug[1];
        }

        const respProm = fetch(fdUrl + "card", {
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        processing = true;

        respProm
          .then(async (resp) => {
            if (resp) {
              if ([201, 202].includes(resp.status)) {
                fdSuccess(resp.status);
                processing = false;

                if (evt.token.card) {
                  const $apCard = document.querySelector("#apCard");
                  $apCard.querySelector("input").value =
                    (evt.token.card.brand ? evt.token.card.brand + " " : "") +
                    "****" +
                    (evt.token.card.last4 || "");
                  $apCard.classList.remove("d-none");
                }

                evt.complete("success");
              } else {
                processing = false;

                try {
                  fdMessages(await resp.text());
                } catch (exc) {
                  fdMessages();
                }

                evt.complete("fail");
              }
            }
          })
          .catch(() => {
            processing = false;
            fdMessages();
            evt.complete("fail");
          });
      });

      const prButton = stripe.elements().create("paymentRequestButton", {
        paymentRequest,
        style: { paymentRequestButton: { type: "donate", height: "38px" } },
      });

      prButton.on("click", () => {
        let valid = true;

        fdEach($fdTransFields, ($field) => {
          if (!$field.validity.valid) {
            valid = false;
            $field.reportValidity();
            return true;
          }
        });

        if (valid) {
          paymentRequest.update({
            currency: $fdCurr.value.toLowerCase(),
            total: {
              label: fdName + (fdInt ? " " + fdInt : ""),
              amount: Math.round(
                parseFloat($fdAmt.value.replace(/,/g, "")) * 100
              ),
            },
          });
        } else {
          paymentRequest.abort();
        }
      });

      prButton.mount("#stripe_pr_btn");

      if (prCanMakePayment.applePay) {
        isStripeApplePay = true;
      } else if (prCanMakePayment.link) {
        document.querySelector(
          "#stripeLinkText"
        ).innerHTML = `To save or use saved payment info <span class="fst-normal">${String.fromCodePoint(
          0x261d
        )}</span>`;
      }

      document.querySelector("#stripe_pr_btn_cont").classList.remove("d-none");
    }

    try {
      var fdIsIframe = window.self !== window.top;
    } catch (e) {
      fdIsIframe = true;
    }

    if (fdIsIframe && PaymentRequest && ApplePaySession && !isStripeApplePay) {
      const $apBtnCont = document.querySelector("#apBtnCont"),
        $apBtn = $apBtnCont.querySelector("#apBtn");

      $apBtn.addEventListener("click", () => {
        const url = new URL(window.location.href);

        url.searchParams.delete("iframe");
        if ($fdAmt.value) url.searchParams.set("amount", $fdAmt.value);
        if ($fdCurr.value) url.searchParams.set("currency", $fdCurr.value);
        if ($fdInt.value) url.searchParams.set("interval", $fdInt.value);

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

        // is this needed? specifically, will this not already be in the url?
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
      });

      $apBtnCont.classList.remove("d-none");
    }
  }
});
