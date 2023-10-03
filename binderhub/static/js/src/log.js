import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';

export function setUpLog() {
  const log = new Terminal({
    convertEol: true,
    disableStdin: true
  });

  const fitAddon = new FitAddon();
  log.loadAddon(fitAddon);
  const logMessages = [];

  log.open(document.getElementById('log'), false);
  fitAddon.fit();

  $(window).resize(function () {
    fitAddon.fit();
  });

  const $panelBody = $("div.panel-body");
  log.show = function () {
    $('#toggle-logs button.toggle').text('hide');
    $panelBody.removeClass('hidden');
  };

  log.hide = function () {
    $('#toggle-logs button.toggle').text('show');
    $panelBody.addClass('hidden');
  };

  log.toggle = function () {
    if ($panelBody.hasClass('hidden')) {
      log.show();
    } else {
      log.hide();
    }
  };

  $('#view-raw-logs').on('click', function (ev) {
    const blob = new Blob([logMessages.join('')], { type: 'text/plain' });
    this.href = window.URL.createObjectURL(blob);
    // Prevent the toggle action from firing
    ev.stopPropagation();
  });

  $('#toggle-logs').click(log.toggle);

  log.writeAndStore = function (msg) {
    logMessages.push(msg);
    log.write(msg);
  };

  return [log, fitAddon];
}
