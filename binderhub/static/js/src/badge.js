export function makeBadgeMarkup(badgeBaseUrl, baseUrl, url, syntax) {
  let badgeImageUrl;

  if (badgeBaseUrl) {
    badgeImageUrl = badgeBaseUrl + "badge_logo.svg";
  } else {
    badgeImageUrl = window.location.origin + baseUrl + "badge_logo.svg";
  }

  if (syntax === 'markdown') {
    return "[![Binder](" + badgeImageUrl + ")](" + url + ")";
  } else if (syntax === 'rst') {
    return ".. image:: " + badgeImageUrl + "\n :target: " + url;

  }
}
