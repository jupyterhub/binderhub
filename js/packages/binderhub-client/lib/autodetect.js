import { fetch as fetchPolyfill } from "whatwg-fetch";

// Use native browser fetch if available, and use the polyfill if not available
// (e.g. in tests https://github.com/jestjs/jest/issues/13834#issuecomment-1407375787)
// @todo: this is only a problem in the jest tests, so get rid of this and mock fetch instead
const fetch = window.fetch || fetchPolyfill;

/**
 * Dict holding cached values of API request to _config endpoint for base URL
 */
let repoProviders = {};

/**
 * Get the repo provider configurations supported by the BinderHub instance
 *
 * @param {URL} baseUrl Base URL to use for constructing path to _config endpoint
 */
export async function getRepoProviders(baseUrl) {
  if (!repoProviders[baseUrl]) {
    const configUrl = new URL("_config", baseUrl);
    const resp = await fetch(configUrl);
    repoProviders[baseUrl] = resp.json();
  }
  return repoProviders[baseUrl];
}

/**
 * Attempt to parse a string (typically a repository URL) into a BinderHub
 * provider/repository/reference/path
 *
 * @param {URL} baseUrl Base URL to use for constructing path to _config endpoint
 * @param {string} text Repository URL or similar to parse
 * @returns {Object} An object if the repository could be parsed with fields
 *   - providerPrefix Prefix denoting what provider was selected
 *   - repository Repository to build
 *   - ref Ref in this repo to build (optional)
 *   - path Path to launch after this repo has been built (optional)
 *   - pathType Type of thing to open path with (raw url, notebook file) (optional)
 *   - providerName User friendly display name of the provider (optional)
 *   null otherwise
 */
export async function detect(baseUrl, text) {
  const config = await getRepoProviders(baseUrl);

  for (const provider in config) {
    const regex_detect = config[provider].regex_detect || [];
    for (const regex of regex_detect) {
      const m = text.match(regex);
      if (m?.groups.repo) {
        return {
          providerPrefix: provider,
          repository: m.groups.repo,
          ref: m.groups.ref,
          path: m.groups.filepath || m.groups.urlpath || null,
          pathType: m.groups.filepath
            ? "filepath"
            : m.groups.urlpath
            ? "urlpath"
            : null,
          providerName: config[provider].display_name,
        };
      }
    }
  }

  return null;
}
