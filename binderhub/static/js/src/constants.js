/**
 * @type {URL}
 * Base URL of this binderhub installation.
 *
 * Guaranteed to have a leading & trailing slash by the binderhub python configuration.
 */
export const BASE_URL = new URL(
  document.getElementById("base-url").dataset.url,
  document.location.origin,
);

const badge_base_url = document.getElementById("badge-base-url").dataset.url;
/**
 * @type {URL}
 * Base URL to use for both badge images as well as launch links.
 *
 * If not explicitly set, will default to BASE_URL. Primarily set up different than BASE_URL
 * when used as part of a federation
 */
export const BADGE_BASE_URL = badge_base_url
  ? new URL(badge_base_url, document.location.origin)
  : BASE_URL;
