import { detect, getRepoProviders } from "@jupyterhub/binderhub-client";
import { updatePathText } from "./path";

/**
 * @param {Object} configDict Dict holding cached values of API request to _config endpoint
 */
function setLabels(configDict) {
  const provider = $("#provider_prefix").val();
  const text = configDict[provider]["text"];
  const tagText = configDict[provider]["tag_text"];
  const refPropDisabled = configDict[provider]["ref_prop_disabled"];
  const labelPropDisabled = configDict[provider]["label_prop_disabled"];
  const placeholder = "HEAD";

  $("#ref").attr("placeholder", placeholder).prop("disabled", refPropDisabled);
  $("label[for=ref]").text(tagText).prop("disabled", labelPropDisabled);
  $("#repository").attr("placeholder", text);
  $("label[for=repository]").text(text);
}

/**
 * Update labels for various inputboxes based on user selection of repo provider
 *
 * @param {URL} baseUrl Base URL to use for constructing path to _config endpoint
 */
export function updateRepoText(baseUrl) {
  getRepoProviders(baseUrl).then(setLabels);
}

/**
 * Attempt to fill in all fields by parsing a pasted repository URL
 *
 * @param {URL} baseUrl Base URL to use for constructing path to _config endpoint
 */
export async function detectPastedRepo(baseUrl) {
  const repoField = $("#repository").val().trim();
  const fields = await detect(baseUrl, repoField);
  // Special case: The BinderHub UI supports https://git{hub,lab}.com/ in the
  // repository (it's stripped out later in the UI).
  // To keep the UI consistent insert it back if it was originally included.
  console.log(fields);
  if (fields) {
    let repo = fields.repository;
    if (repoField.startsWith("https://github.com/")) {
      repo = "https://github.com/" + repo;
    }
    if (repoField.startsWith("https://gitlab.com/")) {
      repo = "https://gitlab.com/" + repo;
    }
    $("#provider_prefix-selected").text(fields.providerName);
    $("#provider_prefix").val(fields.providerPrefix);
    $("#repository").val(repo);
    if (fields.ref) {
      $("#ref").val(fields.ref);
    }
    if (fields.path) {
      $("#filepath").val(fields.path);
      $("#url-or-file-selected").text(
        fields.pathType === "filepath" ? "File" : "URL",
      );
    }
    updatePathText();
    updateRepoText(baseUrl);
  }
}
