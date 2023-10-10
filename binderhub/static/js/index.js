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
import { BASE_URL } from "./src/constants";
import { getBuildFormValues } from "./src/form";
import { updateRepoText } from "./src/repo";

async function build(providerSpec, log, fitAddon, path, pathType) {
  updateFavicon(BASE_URL + "favicon_building.ico");
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
  // If BASE_URL is absolute, use that as the base for build endpoint URL.
  // Else, first resolve BASE_URL relative to current URL, then use *that* as the
  // base for the build endpoint url.
  const buildEndpointUrl = new URL(
    "build",
    new URL(BASE_URL, window.location.href),
  );
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
        updateFavicon(BASE_URL + "favicon_fail.ico");
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
        updateFavicon(BASE_URL + "favicon_success.ico");
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
  updateUrls();

  $("#provider_prefix_sel li").click(function (event) {
    event.preventDefault();

    $("#provider_prefix-selected").text($(this).text());
    $("#provider_prefix").val($(this).attr("value"));
    updateRepoText();
    updateUrls();
  });

  $("#url-or-file-btn")
    .find("a")
    .click(function (evt) {
      evt.preventDefault();

      $("#url-or-file-selected").text($(this).text());
      updatePathText();
      updateUrls();
    });
  updatePathText();
  updateRepoText();

  $("#repository").on("keyup paste change", function () {
    updateUrls();
  });

  $("#ref").on("keyup paste change", function () {
    updateUrls();
  });

  $("#filepath").on("keyup paste change", function () {
    updateUrls();
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
    updateUrls(formValues);
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
