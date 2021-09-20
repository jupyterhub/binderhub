const BASE_URL = $("#base-url").data().url;
const BADGE_BASE_URL = $('#badge-base-url').data().url;
let badge_url;

if (BADGE_BASE_URL) {
  badge_url = BADGE_BASE_URL + "badge_logo.svg";
}
else {
  badge_url = window.location.origin + BASE_URL + "badge_logo.svg";
}

export function markdownBadge(url) {
  // return markdown badge snippet
  return "[![Binder](" + badge_url + ")](" + url + ")";
}

export function rstBadge(url) {
  // return rst badge snippet
  return ".. image:: " + badge_url + "\n :target: " + url;
}
