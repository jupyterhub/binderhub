var BADGE_URL = window.location.origin + BASE_URL + "badge_logo.svg";

export function markdownBadge(url) {
  // return markdown badge snippet
  return "[![Binder](" + BADGE_URL + ")](" + url + ")";
}

export function rstBadge(url) {
  // return rst badge snippet
  return ".. image:: " + BADGE_URL + " :target: " + url;
}
