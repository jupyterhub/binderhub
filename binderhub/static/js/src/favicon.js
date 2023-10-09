/**
 * Dynamically set current page's favicon.
 *
 * @param {String} href Path to Favicon to use
 */
function updateFavicon(href) {
  let link = document.querySelector("link[rel*='icon']");
  if (!link) {
    link = document.createElement("link");
    document.getElementsByTagName("head")[0].appendChild(link);
  }
  link.type = "image/x-icon";
  link.rel = "shortcut icon";
  link.href = href;
}

export { updateFavicon };
