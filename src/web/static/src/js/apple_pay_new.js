/* global
  fdMsgRemaining,
  $fdMsg,
  fdIsOrg,
  $fdIsOrg
*/

const fdUrlParams = new URLSearchParams(window.location.search);

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
