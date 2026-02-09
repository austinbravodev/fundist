/* global Accept, fdFallbackMsg, fdStripePubkey, fdDomains, fdCustomAmounts, fdCurrencies, fdDefCurr, fdDefInt, fdErrorContact, fdTurnstileClientError */

const fdProcOpts = {
		card: {
			authorize_net: {
				attrs: {
					fullName: function () {
						return (
							document.querySelector("#first_name").value.trim() +
							" " +
							document.querySelector("#last_name").value.trim()
						);
					},
					cardNumber: function () {
						return document
							.querySelector("#card_number")
							.value.replace(/\s/g, "");
					},
					month: function () {
						const $mo = document.querySelector("#card_month");

						if ($mo.value.length === 1) {
							$mo.value = "0" + $mo.value;
						}

						return $mo.value;
					},
					year: function () {
						const $year = document.querySelector("#card_year");

						if ($year.value.length === 4) {
							$year.value = $year.value.slice(-2);
						}

						return $year.value;
					},
					cardCode: "card_code",
					zip: "postal_code",
				},
				tokenization: function (data) {
					Accept.dispatchData(
						{
							authData: {
								clientKey:
									"3V8HZ85k96xmca8TE8cje8kz828NC7Uv24Gb55cNjG6s436k3bgLRVMvS5NcpZQ7",
								apiLoginID: "345HZuvN2jpW",
							},
							cardData: data,
						},
						function (resp) {
							if (resp.messages.resultCode === "Error") {
								let msgs = [];
								for (let i = 0; i < resp.messages.message.length; i++) {
									msgs.push(resp.messages.message[i].text);
								}

								fdMessages(msgs);
								fdButton();
							} else {
								fdTransaction({ payment: resp.opaqueData });
							}
						}
					);
				},
			},
			stripe: {
				attrs: {
					"card[name]": function () {
						return (
							document.querySelector("#first_name").value.trim() +
							" " +
							document.querySelector("#last_name").value.trim()
						);
					},
					"card[number]": function () {
						return document
							.querySelector("#card_number")
							.value.replace(/\s/g, "");
					},
					"card[exp_month]": function () {
						const $mo = document.querySelector("#card_month");

						if ($mo.value.length === 1) {
							$mo.value = "0" + $mo.value;
						}

						return $mo.value;
					},
					"card[exp_year]": function () {
						const $year = document.querySelector("#card_year");

						if ($year.value.length === 4) {
							$year.value = $year.value.slice(-2);
						}

						return $year.value;
					},
					"card[cvc]": "card_code",
					"card[address_line1]": "address",
					"card[address_line2]": "unit",
					"card[address_city]": "city",
					"card[address_state]": "province",
					"card[address_zip]": "postal_code",
					"card[address_country]": "country_code",
				},
				tokenization: "https://api.stripe.com/v1/tokens",
				headers: {
					Authorization: "Bearer " + fdStripePubkey,
					"Stripe-Version": "2020-08-27",
				},
				callback: function (req) {
					let resp = JSON.parse(req.responseText);

					if (resp.object === "token") {
						fdTransaction({ payment: resp.id });
					} else {
						fdMessages(resp.error.message);
						fdButton();
					}
				},
			},
		},
	},
	fdProcs = {},
	$fdSubmit = document.querySelector('button[type="submit"]'),
	$fdCurr = document.querySelector("#currency"),
	$fdAmt = document.querySelector("#amount"),
	$fdMeths = document.querySelectorAll('[data-bs-target^="#method-"]'),
	$fdBtnCurrSym = $fdSubmit.querySelector(".curr-sym"),
	$fdBtnInt = $fdSubmit.querySelector("#btn-int"),
	fdUrl = "/transaction/",
	fdNoSupport =
		"Your browser is not supported" +
		(fdFallbackMsg ? " -" + fdFallbackMsg : "."),
	$fdCountry = document.querySelector("#country_code"),
	$fdIsOrg = document.querySelector("#isOrg"),
	$fdMsg = document.querySelector("#message"),
	fdCURRENCIES = new Set(),
	fdBtnsPerks = {},
	$fdIntBtns = document.querySelector("#intervalButtons"),
	$fdCustAmts = document.querySelector("#customAmounts"),
	$fdPerks = document.querySelector("#perks"),
	$turnstileToken = document.querySelector("#turnstileToken");

let fdMsgsType,
	fdMeth,
	$fdInt,
	fdInt,
	fdColls = [],
	fdMsgMax,
	$fdMsgRemaining,
	fdMailingSlug,
	fdCurrentAmt,
	fdIsInterval = false;

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

function fdAmount() {
	let val = "";
	// do you want to reset here?
	fdCurrentAmt = null;

	$fdAmt.setCustomValidity("");
	if ($fdAmt.validity.valid) {
		const tempAmt =
			Math.round(parseFloat($fdAmt.value.replace(/,/g, "")) * 100) / 100;

		if (tempAmt > 0) {
			// do you want to assign here?
			fdCurrentAmt = tempAmt;
			val = tempAmt.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
			$fdBtnCurrSym.classList.remove("d-none");
		}
	}

	$fdSubmit.querySelector("#btn-amt").innerText = $fdAmt.value = val;

	if (!val) {
		$fdBtnCurrSym.classList.add("d-none");
		$fdAmt.setCustomValidity("Please enter a valid amount.");
	}

	$fdAmt.reportValidity();

	fdEach('[name="amounts"]', function ($radio) {
		if (parseFloat($radio.value) === fdCurrentAmt) {
			$radio.checked = true;
			return true;
		}

		$radio.checked = false;
	});
}

function fdChangeCurrSym() {
	fdEach(document.querySelectorAll(".curr-sym"), function ($span) {
		$span.innerText = $fdCurr.options[$fdCurr.selectedIndex].dataset.fdCurrSym;
	});
}

function fdInterval() {
	$fdInt = document.querySelector('[name="interval"]:checked');

	fdInt = $fdInt.nextElementSibling.innerText
		.replace("Once", "")
		.replace("Annual", "Annually");

	$fdBtnInt.innerText = fdInt;
}

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

function fdIsOrg() {
	const $orgGroup = document.querySelector("#orgGroup"),
		$orgName = $orgGroup.querySelector("#organization_name");

	if ($fdIsOrg.checked) {
		$orgName.disabled = false;
		$orgGroup.classList.remove("d-none");
	} else {
		$orgName.disabled = true;
		$orgGroup.classList.add("d-none");
	}
}

function fdMsgRemaining() {
	$fdMsgRemaining.innerText = fdMsgMax - $fdMsg.value.length;
}

/* ---------------------------------- */

function fdGetMeth($el) {
	return $el.getAttribute("data-bs-target").replace("#method-", "");
}

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

function fdSuccess(status, not) {
	fdEach(
		".remove, fieldset.collapse" + (not ? ":not(.show)" : ""),
		function ($fs) {
			$fs.parentNode.removeChild($fs);
		}
	);
	fdEach(".disable, fieldset.collapse", function ($fs) {
		$fs.disabled = true;
	});

	if (status === 202) {
		var type = "info",
			heading = "Pending";
	}

	fdMessages(
		"Please check your email for receipt.",
		type || "success",
		heading || "Confirmed"
	);
}

function fdTransaction(data) {
	fdData(data, "[data-fd-field]");

	if (fdMailingSlug) {
		const mailingSlug = fdMailingSlug.split(" ");

		data.transaction[mailingSlug[0]] = mailingSlug[1];
	}

	fdPost({
		url: fdUrl + fdMeth,
		contentType: "json",
		data: data,
		callback: function (req) {
			if ([201, 202].indexOf(req.status) !== -1) {
				fdSuccess(req.status, true);

				const len = 4,
					$cardNum = document.querySelector("#card_number");
				let new_val = $cardNum.value.slice(-len);

				for (let i = $cardNum.value.length - len; i > 0; i--) {
					new_val = "*" + new_val;
				}

				$cardNum.value = new_val;
			} else {
				fdMessages(req.responseText);
				fdButton();
			}
		},
	});
}

/* -------------------------------------------------------------------------- */

function fdAddPerksIcon($badge) {
	$badge.textContent += " +";
}

const fdOnIntCurrAmtChange = ($newBtns) => {
	const currVal = $fdCurr.value.toLowerCase();
	let assignBtnPerks;

	for (const btnPerks of fdBtnsPerks[$fdInt.value]) {
		const $inpt = btnPerks.button.children[0];

		if (currVal in $inpt.dataset) {
			const btnPerksCurrAmt = parseFloat($inpt.dataset[currVal]);

			if ($newBtns) {
				const $label = btnPerks.button.children[1];

				$inpt.value = $inpt.dataset[currVal];
				$label.childNodes[0].nodeValue = $label.dataset[currVal];

				$inpt.checked =
					Boolean(fdCurrentAmt) && fdCurrentAmt === btnPerksCurrAmt;

				$newBtns.push(btnPerks.button);
			}

			if (fdCurrentAmt && Object.hasOwn(btnPerks, "perks")) {
				if (
					fdCurrentAmt >= btnPerksCurrAmt &&
					(!assignBtnPerks ||
						btnPerksCurrAmt >=
							parseFloat(assignBtnPerks.button.children[0].dataset[currVal]))
				)
					assignBtnPerks = btnPerks;
			}
		}
	}

	if ($newBtns) $fdCustAmts.replaceChildren(...$newBtns);
	assignBtnPerks
		? $fdPerks.replaceChildren(...Object.values(assignBtnPerks.perks))
		: $fdPerks.replaceChildren();
};

/* -------------------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", function () {
	if (fdCustomAmounts) {
		for (const intBtns of fdCustomAmounts.split("~~").filter((i) => i)) {
			const [int, btns] = intBtns.split("||"),
				intKey = int.trim().toLowerCase();

			if (["once", "month", "year"].includes(intKey)) {
				const $intInpt = document.createElement("input"),
					$intLabel = document.createElement("label");

				fdBtnsPerks[intKey] = [];

				for (let btn of btns.split("//").filter((i) => i)) {
					let label, perksTitle, perks;

					const btnPerks = { button: document.createElement("div") },
						seps = ["|", "=", "~"]
							.filter((sep) => btn.includes(sep))
							.sort((sep, pSep) => btn.indexOf(pSep) - btn.indexOf(sep)),
						$input = document.createElement("input"),
						$label = document.createElement("label"),
						$badge = document.createElement("span");

					for (const sep of seps) {
						let content;
						[btn, content] = btn.split(sep);

						if (sep === "|") {
							label = content.trim();
						} else if (sep === "=") {
							perksTitle = content.trim();
						} else if (sep === "~") {
							perks = content.split(";").filter((i) => i);
						}
					}

					btnPerks.button.className = "col" + (label ? " amtBtnLabelled" : "");

					$input.type = "radio";
					$input.className = "btn-check";
					$input.name = "amounts";
					$input.id = "amt";
					$input.autocomplete = "off";

					for (const amt of btn.split(",").filter((i) => i)) {
						const [val, curr] = amt
							.trim()
							.toLowerCase()
							.match(/^([0-9.]+)\s*([a-z]{3})$/)
							.slice(1, 3);

						if (Object.hasOwn(fdCurrencies, curr)) {
							$label.dataset[curr] =
								fdCurrencies[curr] +
								parseFloat(val)
									.toFixed(2)
									.replace(/\B(?=(\d{3})+(?!\d))/g, ",")
									.replace(".00", "");

							$input.dataset[curr] = val;
							$input.id += "-" + val + curr;

							fdCURRENCIES.add(curr);
						}
					}

					btnPerks.button.appendChild($input);

					$label.className =
						"btn btn-outline-primary bg-white-unimportant d-flex justify-content-center align-items-center flex-wrap";
					$label.htmlFor = $input.id;

					$label.appendChild(document.createTextNode(""));

					if (label) $badge.textContent = label;

					if (perks || perksTitle) {
						const $perksHeading = document.createElement("h5");

						$perksHeading.className = "alert-heading fw-bold mb-0";

						btnPerks.perks = { title: $perksHeading };
						btnPerks.perks.title.textContent =
							perksTitle || label || "Your Donation Includes:";
						fdAddPerksIcon($badge);
					}

					if ($badge.textContent) {
						$badge.className = "badge bg-primary";
						$label.appendChild($badge);
					}

					btnPerks.button.appendChild($label);

					if (perks) {
						btnPerks.perks.list = document.createElement("ul");
						btnPerks.perks.list.className =
							"list-unstyled position-relative mb-n1 mt-2 pt-2";

						for (const perk of perks) {
							const $perk = document.createElement("li"),
								$perkIcon = document.createElement("span");

							$perk.className = "mb-1";
							$perkIcon.className = "me-2";
							$perkIcon.textContent = String.fromCodePoint(0x2705);

							$perk.replaceChildren(
								$perkIcon,
								document.createTextNode(perk.trim())
							);

							btnPerks.perks.list.appendChild($perk);
						}
					}

					btnPerks.button.addEventListener("click", () => {
						$fdAmt.value = $input.value;
						fdAmount();
						fdOnIntCurrAmtChange();
					});

					fdBtnsPerks[intKey].push(btnPerks);
				}

				$intInpt.type = "radio";
				$intInpt.className = "btn-check";
				$intInpt.name = "interval";
				$intInpt.id = "interval-" + intKey;
				$intInpt.value = intKey;
				$intInpt.autocomplete = "off";
				$intInpt.required = true;
				if (intKey !== "once") $intInpt.dataset.fdField = "transaction";
				if (fdDefInt === intKey) fdIsInterval = $intInpt.checked = true;

				$fdIntBtns.appendChild($intInpt);

				$intLabel.className = "btn btn-input flex-basis-0";
				$intLabel.htmlFor = "interval-" + intKey;
				$intLabel.textContent = ((intLabel) =>
					intLabel[0].toUpperCase() + intLabel.slice(1))(
					intKey.replace("month", "monthly").replace("year", "annual")
				);

				$fdIntBtns.appendChild($intLabel);
			}
		}

		for (const int in fdBtnsPerks) {
			for (const btnPerks of fdBtnsPerks[int]) {
				if (!Object.hasOwn(btnPerks, "perks")) {
					for (const _btnPerks of fdBtnsPerks[int]) {
						if (Object.hasOwn(_btnPerks, "perks")) {
							let hasPerks = true;
							const inptDataset = btnPerks.button.children[0].dataset;

							for (const curr in inptDataset) {
								const _inptDataset = _btnPerks.button.children[0].dataset;

								if (
									!(curr in _inptDataset) ||
									parseFloat(inptDataset[curr]) < parseFloat(_inptDataset[curr])
								) {
									hasPerks = false;
									break;
								}
							}

							if (hasPerks) {
								fdAddPerksIcon(btnPerks.button.children[1].childNodes[1]);
								break;
							}
						}
					}
				}
			}
		}

		if (!fdIsInterval) $fdIntBtns.firstElementChild.checked = true;
		if (
			Object.keys(fdBtnsPerks).length === 1 &&
			Object.hasOwn(fdBtnsPerks, "once")
		)
			$fdIntBtns.style.display = "none";
		if (fdCURRENCIES.size === 1) $fdCurr.disabled = true;

		fdCURRENCIES.forEach((curr) => {
			const $opt = document.createElement("option");

			$opt.value = $opt.textContent = curr.toUpperCase();
			$opt.dataset.fdCurrSym = fdCurrencies[curr];
			if (fdDefCurr === curr) $opt.selected = true;

			$fdCurr.appendChild($opt);
		});

		if ($fdCurr.selectedIndex === -1) $fdCurr.options[0].selected = true;
		fdChangeCurrSym();
	}

	if ($fdAmt.value) fdAmount();
	fdInterval();
	if (fdCustomAmounts) fdOnIntCurrAmtChange([]);

	$fdCurr.addEventListener("change", function () {
		fdChangeCurrSym();
		if (fdCustomAmounts) fdOnIntCurrAmtChange([]);
	});
	fdEach('[name="interval"]', function ($radio) {
		$radio.addEventListener("change", () => {
			fdInterval();
			if (fdCustomAmounts) fdOnIntCurrAmtChange([]);
		});
	});
	$fdAmt.addEventListener("blur", () => {
		fdAmount();
		if (fdCustomAmounts) fdOnIntCurrAmtChange();
	});

	if (!fdCustomAmounts) {
		fdEach('[name="amounts"] + label', function ($btn) {
			$btn.addEventListener("click", function () {
				$fdAmt.value = $btn.previousElementSibling.value;
				fdAmount();
			});
		});
	}

	const fdUrlParams = new URLSearchParams(window.location.search);

	if ($fdIsOrg) {
		const orgName = fdUrlParams.get("organization_name");

		if (orgName) {
			document.querySelector("#organization_name").value = orgName;
			$fdIsOrg.checked = true;
			fdIsOrg();
		}

		$fdIsOrg.addEventListener("change", fdIsOrg);
	}

	if ($fdMsg) {
		fdMsgMax = parseInt($fdMsg.getAttribute("maxlength"));
		$fdMsgRemaining = $fdMsg.parentElement.nextElementSibling.firstChild;

		const msg = fdUrlParams.get("message");

		if (msg) {
			$fdMsg.value = msg;
		}

		fdMsgRemaining();
		$fdMsg.addEventListener("input", fdMsgRemaining);
	}

	fdEach("[data-fd-methods]", function ($fs) {
		// eslint-disable-next-line no-undef
		let coll = new bootstrap.Collapse($fs, { toggle: false });

		coll.fdMeths = $fs.dataset.fdMethods.split(" ");
		fdColls.push(coll);
	});

	fdEach("fieldset.collapse", function ($fs) {
		$fs.addEventListener("show.bs.collapse", function () {
			$fs.disabled = false;
		});

		$fs.addEventListener("hide.bs.collapse", function () {
			$fs.disabled = true;
		});
	});

	fdEach($fdMeths, function ($btn) {
		const meth = fdGetMeth($btn);
		fdProcs[meth] = fdProcOpts[meth][$btn.dataset.fdProc];

		$btn.addEventListener("click", function () {
			fdMeth = null;

			fdEach($fdMeths, function ($clickedBtn) {
				if ($clickedBtn.getAttribute("aria-expanded") === "true") {
					fdMeth = fdGetMeth($clickedBtn);
					return true;
				}
			});

			for (let i = 0; i < fdColls.length; i++) {
				fdColls[i].fdMeths.indexOf(fdMeth) !== -1
					? fdColls[i].show()
					: fdColls[i].hide();
			}
		});
	});

	fdCountry();
	$fdCountry.addEventListener("change", fdCountry);

	if (document.location.protocol !== "https:") {
		fdMessages("A secure connection is required to use this form.");
	} else if (!("withCredentials" in new XMLHttpRequest())) {
		fdMessages(fdNoSupport);
	} else {
		window.addEventListener("message", (ev) => {
			if (fdDomains.includes(ev.origin) && ev.data.startsWith("mailing_slug")) {
				fdMailingSlug = ev.data;
			}
		});

		window.parent.postMessage("listening", "*");

		document.querySelector("form").addEventListener("submit", function (e) {
			e.preventDefault();
			fdButton();

			if (true) {
				let attrs = fdProcs[fdMeth].attrs,
					data = {};

				fdIterObj(attrs, function (attr) {
					let val = attrs[attr];

					if (typeof val === "function") {
						data[attr] = val();
					} else {
						const $field = document.querySelector("#" + val);

						if ($field && !$field.disabled) {
							data[attr] = $field.value.trim();
						}
					}
				});

				try {
					if (typeof fdProcs[fdMeth].tokenization === "string") {
						fdPost({
							url: fdProcs[fdMeth].tokenization,
							headers: fdProcs[fdMeth].headers,
							data: data,
							callback: fdProcs[fdMeth].callback,
						});
					} else {
						fdProcs[fdMeth].tokenization(data);
					}
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
