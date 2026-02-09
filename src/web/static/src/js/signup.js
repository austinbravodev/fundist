/* global fdFallbackMsg, fdPetition, fdErrorContact, fdTurnstileClientError */

const $fdSubmit = document.querySelector('button[type="submit"]'),
  fdNoSupport =
    "Your browser is not supported" +
    (fdFallbackMsg ? " -" + fdFallbackMsg : "."),
  $fdCountry = document.querySelector("#country_code"),
  $fdMsg = document.querySelector("#message"),
  $turnstileToken = document.querySelector("#turnstileToken");

let fdMsgsType, fdMsgMax, $fdMsgRemaining;

/* -------------------------------------------------------------------------- */

function fdEach(els, func) {
  const $els = typeof els === "string" ? document.querySelectorAll(els) : els;

  for (let i = 0; i < $els.length; i++) {
    if (func($els[i])) break;
  }
}

function fdIterObj(data, func) {
  for (let attr in data) {
    // eslint-disable-next-line no-prototype-builtins
    if (data.hasOwnProperty(attr)) {
      func(attr);
    }
  }
}

function fdMessages(msgs, type, heading) {
  const $msgs = document.querySelector("#messages"),
    open = '<hr class="my-2"><p class="mb-0">',
    close = "</p>" + (((!type || type === "danger") && fdErrorContact) || "");

  if (fdMsgsType) $msgs.classList.remove(fdMsgsType);
  fdMsgsType = "alert-" + (type || "danger");

  $msgs.classList.add(fdMsgsType);
  $msgs.innerHTML =
    '<h4 class="alert-heading">' +
    (heading || "Error" + (Array.isArray(msgs) && msgs.length > 1 ? "s" : "")) +
    "</h4>" +
    open +
    (msgs
      ? typeof msgs === "string"
        ? msgs
        : msgs.join(close + open)
      : "An error occurred - please reload the page and try again." +
        (fdFallbackMsg ? " If the problem persists," + fdFallbackMsg : "")) +
    close;
}

function fdButton() {
  const $icon = $fdSubmit.querySelector(".btn-icon-d-sibling-toggle");

  if ($fdSubmit.disabled) {
    $icon.classList.remove("d-none");
    $fdSubmit.disabled = false;
  } else {
    $icon.classList.add("d-none");
    $fdSubmit.disabled = true;
  }
}

function fdParams(data) {
  let params = [];

  fdIterObj(data, function (attr) {
    params.push(attr + "=" + encodeURIComponent(data[attr]));
  });

  return params.join("&");
}

function fdPost(_req) {
  let req = new XMLHttpRequest();

  if (_req.callback) {
    req.onreadystatechange = function () {
      try {
        if (req.readyState === 4) {
          _req.callback(req);
        }
      } catch (exc) {
        fdMessages();
        fdButton();
      }
    };
  }

  req.open("POST", _req.url);

  if (_req.headers) {
    fdIterObj(_req.headers, function (header) {
      req.setRequestHeader(header, _req.headers[header]);
    });
  }
  req.setRequestHeader(
    "Content-Type",
    "application/" + (_req.contentType || "x-www-form-urlencoded")
  );
  req.setRequestHeader("Cache-Control", "no-cache, no-store");
  req.send(
    (_req.contentType === "json" ? JSON.stringify : fdParams)(_req.data)
  );
}

/* ---------------------------------- */

function fdCountry() {
  const $province = document.querySelector("#province");
  let provDisabled = true;

  $province.querySelectorAll("optgroup").forEach(($og) => {
    if ($og.id == "opts-" + $fdCountry.value) {
      $og.querySelector("option").selected = true;
      provDisabled = $og.disabled = false;
      $og.classList.remove("d-none");
    } else {
      $og.disabled = true;
      $og.classList.add("d-none");
    }
  });

  $province.disabled = provDisabled;

  if (provDisabled) {
    $province.classList.add("d-none");
  } else {
    $province.classList.remove("d-none");
  }
}

function fdMsgRemaining() {
  $fdMsgRemaining.innerText = fdMsgMax - $fdMsg.value.length;
}

/* ---------------------------------- */

function fdData(data, sel) {
  fdEach(
    sel,
    function ($field) {
      if (!$field.disabled && ($field.type !== "radio" || $field.checked)) {
        this[$field.dataset.fdField] = this[$field.dataset.fdField] || {};
        this[$field.dataset.fdField][$field.name || $field.id] = $field.value;
      }
    }.bind(data)
  );
}

function fdSuccess() {
  fdEach(".remove", function ($fs) {
    $fs.parentNode.removeChild($fs);
  });
  fdEach(".disable", function ($fs) {
    $fs.disabled = true;
  });

  fdMessages("Thanks for signing" + fdPetition + ".", "success", "Confirmed");
}

/* -------------------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
  if ($fdMsg) {
    fdMsgMax = parseInt($fdMsg.getAttribute("maxlength"));
    $fdMsgRemaining = $fdMsg.parentElement.nextElementSibling.firstChild;

    fdMsgRemaining();
    $fdMsg.addEventListener("input", fdMsgRemaining);
  }

  fdCountry();
  $fdCountry.addEventListener("change", fdCountry);

  if (document.location.protocol !== "https:") {
    fdMessages("A secure connection is required to use this form.");
  } else if (!("withCredentials" in new XMLHttpRequest())) {
    fdMessages(fdNoSupport);
  } else {
    document.querySelector("form").addEventListener("submit", function (e) {
      e.preventDefault();
      fdButton();

      if (true) {
        let data = {};

        fdData(data, document.querySelectorAll("[data-fd-field]"));

        // Checkbox Tags
        const checkboxTagsArr = document
          .querySelector("#tagCheckboxes")
          ?.querySelectorAll("input");

        if (checkboxTagsArr) {
          const checkboxTags = [...checkboxTagsArr]
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) =>
              typeof checkbox.value === "string"
                ? checkbox.value.trim()
                : checkbox.value
            )
            .join(",");

          data.transaction = data.transaction || {};

          data.transaction.fundist_tags = `${
            data.transaction.fundist_tags || ""
          },${checkboxTags}`;
        }
        // Checkbox Tags

        try {
          fdPost({
            url: "/signup/",
            contentType: "json",
            data: data,
            callback: function (req) {
              if (req.status == 202) {
                fdSuccess();
              } else {
                fdMessages(req.responseText);
                fdButton();
              }
            },
          });
        } catch (exc) {
          fdMessages();
          fdButton();
        }
      } else {
        fdMessages(fdTurnstileClientError);
        fdButton();
      }
    });

    fdButton();
  }
});
