/* global turnstile, fdMessages, fdNoSupport, fdTurnstileSiteKey, $turnstileToken */

let fdTurnstileError = null;

window.onloadTurnstileCallback = () => {
  const $turnstileContainer = document.querySelector("#turnstileContainer");

  turnstile.render($turnstileContainer, {
    sitekey: fdTurnstileSiteKey,
    action: $turnstileContainer.dataset.turnstileAction,
    callback: (token) => {
      $turnstileToken.value = token;
      $turnstileContainer.classList.add("d-none");
    },
    "error-callback": (err) => {
      if (err !== fdTurnstileError) {
        fetch("/log/", {
          method: "POST",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            errors: [{ type: "turnstile", message: err }],
          }),
        }).then((res) => {
          if (res.status === 201) {
            fdTurnstileError = err;
            console.log("Turnstile error was logged.");
          } else {
            console.log("Turnstile error was not logged.");
          }
        });
      }
    },
    "expired-callback": () => {
      $turnstileContainer.classList.remove("d-none");
    },
    "unsupported-callback": () => {
      fdMessages(fdNoSupport);
    },
    "response-field": false,
  });
};
