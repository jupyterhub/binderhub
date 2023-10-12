/**
 * Generate markdown that people can put on their README or documentation to link to this binder
 *
 * @param {string} badgeBaseUrl Optional base URL to use for badge images. If not passed, current origin + baseUrl is used
 * @param {string} baseUrl Base URL of this binderhub installation. Used only if badgeBaseUrl is not passed
 * @param {string} url Link target URL that represents this binder installation
 * @param {string} syntax Kind of markup to generate. Supports 'markdown' and 'rst'
 * @returns {string}
 */
export function makeBadgeMarkup(badgeBaseUrl, baseUrl, url, syntax) {
  let badgeImageUrl;

  if (badgeBaseUrl) {
    badgeImageUrl = badgeBaseUrl + "badge_logo.svg";
  } else {
    badgeImageUrl = window.location.origin + baseUrl + "badge_logo.svg";
  }

  if (syntax === "markdown") {
    return "[![Binder](" + badgeImageUrl + ")](" + url + ")";
  } else if (syntax === "rst") {
    return ".. image:: " + badgeImageUrl + "\n :target: " + url;
  }
}
