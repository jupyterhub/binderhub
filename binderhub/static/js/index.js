/* If this file gets over 200 lines of code long (not counting docs / comments), start using a framework
 */
import ClipboardJS from "clipboard";
import "event-source-polyfill";

import { BinderRepository } from "@jupyterhub/binderhub-client";
import { updatePathText } from "./src/path";
import { nextHelpText } from "./src/loading";
import { updateFavicon } from "./src/favicon";

import "xterm/css/xterm.css";

// Include just the bootstrap components we use
import "bootstrap/js/dropdown";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/css/bootstrap-theme.min.css";

import "../index.css";
import { setUpLog } from "./src/log";
import { updateUrls } from "./src/urls";
import { getBuildFormValues } from "./src/form";
import { updateRepoText } from "./src/repo";

/**
 * @type {URL}
 * Base URL of this binderhub installation.
 *
 * Guaranteed to have a leading & trailing slash by the binderhub python configuration.
 */
const BASE_URL = new URL(
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
const BADGE_BASE_URL = badge_base_url
  ? new URL(badge_base_url, document.location.origin)
  : BASE_URL;

async function build(providerSpec, log, fitAddon, path, pathType) {
  updateFavicon(new URL("favicon_building.ico", BASE_URL));
  // split provider prefix off of providerSpec
  const spec = providerSpec.slice(providerSpec.indexOf("/") + 1);
  // Update the text of the loading page if it exists
  if ($("div#loader-text").length > 0) {
    $("div#loader-text p.launching").text(
      "Starting repository: " + decodeURIComponent(spec),
    );
  }

  $("#build-progress .progress-bar").addClass("hidden");
  log.clear();

  $(".on-build").removeClass("hidden");

  const buildToken = $("#build-token").data("token");
  const buildEndpointUrl = new URL("build", BASE_URL);
  const image = new BinderRepository(
    providerSpec,
    buildEndpointUrl,
    buildToken,
  );

  for await (const data of image.fetch()) {
    // Write message to the log terminal if there is a message
    if (data.message !== undefined) {
      log.writeAndStore(data.message);
      fitAddon.fit();
    } else {
      console.log(data);
    }

    switch (data.phase) {
      case "waiting": {
        $("#phase-waiting").removeClass("hidden");
        break;
      }
      case "building": {
        $("#phase-building").removeClass("hidden");
        log.show();
        break;
      }
      case "pushing": {
        $("#phase-pushing").removeClass("hidden");
        break;
      }
      case "failed": {
        $("#build-progress .progress-bar").addClass("hidden");
        $("#phase-failed").removeClass("hidden");

        $("#loader").addClass("paused");

        // If we fail for any reason, show an error message and logs
        updateFavicon(new URL("favicon_fail.ico", BASE_URL));
        log.show();
        if ($("div#loader-text").length > 0) {
          $("#loader").addClass("error");
          $("div#loader-text p.launching").html(
            "Error loading " + spec + "!<br /> See logs below for details.",
          );
        }
        image.close();
        break;
      }
      case "built": {
        $("#phase-already-built").removeClass("hidden");
        $("#phase-launching").removeClass("hidden");
        updateFavicon(new URL("favicon_success.ico", BASE_URL));
        break;
      }
      case "ready": {
        image.close();
        // If data.url is an absolute URL, it'll be used. Else, it'll be interpreted
        // relative to current page's URL.
        const serverUrl = new URL(data.url, window.location.href);
        // user server is ready, redirect to there
        window.location.href = image.getFullRedirectURL(
          serverUrl,
          data.token,
          path,
          pathType,
        );
        break;
      }
      default: {
        console.log("Unknown phase in response from server");
        console.log(data);
        break;
      }
    }
  }
  return image;
}

function indexMain() {
  const [log, fitAddon] = setUpLog();

  // setup badge dropdown and default values.
  updateUrls(BADGE_BASE_URL);

  $("#provider_prefix_sel li").click(function (event) {
    event.preventDefault();

    $("#provider_prefix-selected").text($(this).text());
    $("#provider_prefix").val($(this).attr("value"));
    updateRepoText(BASE_URL);
    updateUrls(BADGE_BASE_URL);
  });

  $("#url-or-file-btn")
    .find("a")
    .click(function (evt) {
      evt.preventDefault();

      $("#url-or-file-selected").text($(this).text());
      updatePathText();
      updateUrls(BADGE_BASE_URL);
    });
  updatePathText();
  updateRepoText(BASE_URL);

  $("#repository").on("keyup paste change", function () {
    updateUrls(BADGE_BASE_URL);
  });

  $("#ref").on("keyup paste change", function () {
    updateUrls(BADGE_BASE_URL);
  });

  $("#filepath").on("keyup paste change", function () {
    updateUrls(BADGE_BASE_URL);
  });

  $("#toggle-badge-snippet").on("click", function () {
    const badgeSnippets = $("#badge-snippets");
    if (badgeSnippets.hasClass("hidden")) {
      badgeSnippets.removeClass("hidden");
      $("#badge-snippet-caret").removeClass("glyphicon-triangle-right");
      $("#badge-snippet-caret").addClass("glyphicon-triangle-bottom");
    } else {
      badgeSnippets.addClass("hidden");
      $("#badge-snippet-caret").removeClass("glyphicon-triangle-bottom");
      $("#badge-snippet-caret").addClass("glyphicon-triangle-right");
    }

    return false;
  });

  $("#build-form").submit(async function (e) {
    e.preventDefault();
    const formValues = getBuildFormValues();
    updateUrls(BADGE_BASE_URL, formValues);
    await build(
      formValues.providerPrefix + "/" + formValues.repo + "/" + formValues.ref,
      log,
      fitAddon,
      formValues.path,
      formValues.pathType,
    );
  });
}

async function loadingMain(providerSpec) {
  const [log, fitAddon] = setUpLog();
  // retrieve (encoded) filepath/urlpath from URL
  // URLSearchParams.get returns the decoded value,
  // that is good because it is the real value and '/'s will be trimmed in `launch`
  const params = new URL(location.href).searchParams;
  let pathType, path;
  path = params.get("urlpath");
  if (path) {
    pathType = "url";
  } else {
    path = params.get("labpath");
    if (path) {
      pathType = "lab";
    } else {
      path = params.get("filepath");
      if (path) {
        pathType = "file";
      }
    }
  }
  await build(providerSpec, log, fitAddon, path, pathType);

  // Looping through help text every few seconds
  const launchMessageInterval = 6 * 1000;
  setInterval(nextHelpText, launchMessageInterval);

  // If we have a long launch, add a class so we display a long launch msg
  const launchTimeout = 120 * 1000;
  setTimeout(() => {
    $("div#loader-links p.text-center").addClass("longLaunch");
    nextHelpText();
  }, launchTimeout);

  return false;
}

// export entrypoints
window.loadingMain = loadingMain;
window.indexMain = indexMain;

// Load the clipboard after the page loads so it can find the buttons it needs
window.onload = function () {
  new ClipboardJS(".clipboard");
};
