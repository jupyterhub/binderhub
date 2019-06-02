var BASE_URL = $("#base-url").data().url;
var BADGE_BASE_URL = $('#badge-base-url').data().url;

if (BADGE_BASE_URL) {
  var BADGE_URL = BADGE_BASE_URL + "badge_logo.svg";
}
else {
  var BADGE_URL = window.location.origin + BASE_URL + "badge_logo.svg";
}

export function markdownBadge(url) {
  // return markdown badge snippet
  return "[![Binder](" + BADGE_URL + ")](" + url + ")";
}

export function rstBadge(url) {
  // return rst badge snippet
  return ".. image:: " + BADGE_URL + "\n :target: " + url;
}
