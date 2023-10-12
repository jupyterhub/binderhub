import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";

/**
 * Set up a read only xterm.js based terminal, augmented with some additional methods, to display log lines
 *
 * @returns Array of the xterm.js instance to write to, and a FitAddon instance to use for resizing the xterm appropriately
 */
export function setUpLog() {
  const log = new Terminal({
    convertEol: true,
    disableStdin: true,
  });

  const fitAddon = new FitAddon();
  log.loadAddon(fitAddon);
  const logMessages = [];

  log.open(document.getElementById("log"), false);
  fitAddon.fit();

  $(window).resize(function () {
    fitAddon.fit();
  });

  const $panelBody = $("div.panel-body");

  /**
   * Show the log terminal
   */
  log.show = function () {
    $("#toggle-logs button.toggle").text("hide");
    $panelBody.removeClass("hidden");
  };

  /**
   * Hide the log terminal
   */
  log.hide = function () {
    $("#toggle-logs button.toggle").text("show");
    $panelBody.addClass("hidden");
  };

  /**
   * Toggle visibility of the log terminal
   */
  log.toggle = function () {
    if ($panelBody.hasClass("hidden")) {
      log.show();
    } else {
      log.hide();
    }
  };

  $("#view-raw-logs").on("click", function (ev) {
    const blob = new Blob([logMessages.join("")], { type: "text/plain" });
    this.href = window.URL.createObjectURL(blob);
    // Prevent the toggle action from firing
    ev.stopPropagation();
  });

  $("#toggle-logs").click(log.toggle);

  /**
   * Write message to xterm and store it in the download buffer
   *
   * @param {string} msg Message to write to the terminal & add to message buffer
   */
  log.writeAndStore = function (msg) {
    logMessages.push(msg);
    log.write(msg);
  };

  return [log, fitAddon];
}
