import { getBuildFormValues } from "./form";
import {
  makeShareableBinderURL,
  makeBadgeMarkup,
} from "@jupyterhub/binderhub-client";

/**
 * Update the shareable URL and badge snippets in the UI based on values user has entered in the form
 */
export function updateUrls(publicBaseUrl, formValues) {
  if (typeof formValues === "undefined") {
    formValues = getBuildFormValues();
  }
  if (formValues.repo) {
    const url = makeShareableBinderURL(
      publicBaseUrl,
      formValues.providerPrefix,
      formValues.repo,
      formValues.ref,
      formValues.path,
      formValues.pathType,
    );

    // update URLs and links (badges, etc.)
    $("#badge-link").attr("href", url);
    $("#basic-url-snippet").text(url);
    $("#markdown-badge-snippet").text(
      makeBadgeMarkup(publicBaseUrl, url, "markdown"),
    );
    $("#rst-badge-snippet").text(makeBadgeMarkup(publicBaseUrl, url, "rst"));
  } else {
    ["#basic-url-snippet", "#markdown-badge-snippet", "#rst-badge-snippet"].map(
      function (item) {
        const el = $(item);
        el.text(el.attr("data-default"));
      },
    );
  }
}
