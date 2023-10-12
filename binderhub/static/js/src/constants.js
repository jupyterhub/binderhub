/**
 * @type {string}
 * Base URL of this binderhub installation
 */
export const BASE_URL = $("#base-url").data().url;

/**
 * @type {string}
 * Optional base URL to use for both badge images as well as launch links.
 *
 * Is different from BASE_URL primarily when used as part of a federation.
 */
export const BADGE_BASE_URL = $("#badge-base-url").data().url;
