import { makeBadgeMarkup } from "./badge";
import { getBuildFormValues } from "./form";
import { BADGE_BASE_URL, BASE_URL } from "./constants";

/**
 * Generate a shareable binder URL for given repository

 * @param {string} providerPrefix prefix denoting what provider was selected
 * @param {string} repo repo to build
 * @param {[string]} ref optional ref in this repo to build
 * @param {string} path Path to launch after this repo has been built
 * @param {string} pathType Type of thing to open path with (raw url, notebook file, lab, etc)
 *
 * @returns {string|null} A URL that can be shared with others, and clicking which will launch the repo
 */
function v2url(providerPrefix, repository, ref, path, pathType) {
  // return a v2 url from a providerPrefix, repository, ref, and (file|url)path
  if (repository.length === 0) {
    // no repo, no url
    return null;
  }
  let url;
  if (BADGE_BASE_URL) {
    url =
      BADGE_BASE_URL + "v2/" + providerPrefix + "/" + repository + "/" + ref;
  } else {
    url =
      window.location.origin +
      BASE_URL +
      "v2/" +
      providerPrefix +
      "/" +
      repository +
      "/" +
      ref;
  }
  if (path && path.length > 0) {
    // encode the path, it will be decoded in loadingMain
    url = url + "?" + pathType + "path=" + encodeURIComponent(path);
  }
  return url;
}

/**
 * Update the shareable URL and badge snippets in the UI based on values user has entered in the form
 */
export function updateUrls(formValues) {
  if (typeof formValues === "undefined") {
    formValues = getBuildFormValues();
  }
  const url = v2url(
    formValues.providerPrefix,
    formValues.repo,
    formValues.ref,
    formValues.path,
    formValues.pathType,
  );

  if ((url || "").trim().length > 0) {
    // update URLs and links (badges, etc.)
    $("#badge-link").attr("href", url);
    $("#basic-url-snippet").text(url);
    $("#markdown-badge-snippet").text(
      makeBadgeMarkup(BADGE_BASE_URL, BASE_URL, url, "markdown"),
    );
    $("#rst-badge-snippet").text(
      makeBadgeMarkup(BADGE_BASE_URL, BASE_URL, url, "rst"),
    );
  } else {
    ["#basic-url-snippet", "#markdown-badge-snippet", "#rst-badge-snippet"].map(
      function (item) {
        const el = $(item);
        el.text(el.attr("data-default"));
      },
    );
  }
}
