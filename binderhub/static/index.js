/* If this file gets over 200 lines of code long (not counting docs / comments), start using a framework
  State transitions that are valid are:
  start -> waiting
  start -> built
  start -> failed
  waiting -> building
  waiting -> failed
  building -> pushing
  building -> failed
  pushing -> built
  pushing -> failed
*/

function Image(provider, spec) {
    this.provider = provider;
    this.spec = spec;
    this.callbacks = {};
    this.state = null;
}

Image.prototype.onStateChange = function(state, cb) {
    if (this.callbacks[state] === undefined) {
        this.callbacks[state] = [cb];
    } else {
        this.callbacks[state].push(cb);
    }
};

Image.prototype.changeState = function(state, data) {
    if (this.callbacks[state] !== undefined) {
        for (var i = 0; i < this.callbacks[state].length; i++) {
            this.callbacks[state][i](this.state, state, data);
        }
    }
    if (this.callbacks['*'] !== undefined) {
        for (var i = 0; i < this.callbacks['*'].length; i++) {
            this.callbacks['*'][i](this.state, state, data);
        }
    }

    // FIXME: Make sure this this is a valid state transition!
    this.state = state;
}

Image.prototype.fetch = function() {
    var apiUrl = '/build/' + this.provider + '/' + this.spec;
    this.eventSource = new EventSource(apiUrl);
    var that = this;
    this.eventSource.onerror = function (err) {
        console.error("Failed to construct event stream", err);
        that.changeState("failed", {"message": "Failed to connect to event stream\n"});
    };
    this.eventSource.addEventListener('message', function(event) {
        var data = JSON.parse(event.data);
        // FIXME: Rename 'phase' to 'state' upstream
        // FIXME: fix case of phase/state upstream
        var state = data.phase.toLowerCase();
        that.changeState(state, data);
    });
};

Image.prototype.close = function() {
    if (this.eventSource !== undefined) {
        this.eventSource.close();
    }
};

Image.prototype.launch = function(url, token, filepath) {
    // redirect a user to a running server with a token
    if (filepath) {
      // strip trailing /
      url = url.replace(/\/$/, '');
      // /tree is safe because it allows redirect to files
      url = url + '/tree/' + encodeURI(filepath);
    }
    url = url + '?' + $.param({token: token});
    window.location.href = url;
};


function v2url(repository, ref, filepath) {
  // return a v2 url from a repository, ref, and filepath
  if (repository.length === 0) {
    // no repo, no url
    return null;
  }
  var url = window.location.origin + '/v2/gh/' + repository + '/' + ref;
  if (filepath && filepath.length > 0) {
    url = url + '?filepath=' + encodeURIComponent(filepath);
  }
  return url;
}


function updateUrl() {
  // update URLs and links (badges, etc.)
  var repo = $('#repository').val().trim();
  repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
  // trim trailing or leading '/' on repo
  repo = repo.replace(/(^\/)|(\/?$)/g, '');
  var ref = $('#ref').val().trim();
  var filepath = $('#filepath').val().trim();
  var url = v2url(repo, ref, filepath);
  // update URL references
  $("#badge-link").attr('href', url);
  return url;
}


var BADGE_URL = window.location.origin + '/badge.svg'


function markdownBadge(url) {
  // return markdown badge snippet
  return '[![Binder](' + BADGE_URL + ')](' + url + ')'
}


function rstBadge(url) {
  // return rst badge snippet
  return '.. image:: ' + BADGE_URL + ' :target: ' + url
}

$(function(){
    var failed = false;
    var logsVisible = false;
    var log = new Terminal({
        convertEol: true,
        disableStdin: true
    });

    // setup badge dropdown
    updateUrl();

    // start the badge invisible
    $('#badge-snippet').hide();
    $('#launch-buttons').on('hidden.bs.dropdown', function () {
      // hide the badge snippet when dismissing the dropdown
      $('#badge-snippet').hide();
    });

    $('#markdown-badge-toggle').on('click', function () {
      var url = updateUrl();
      $('#badge-snippet')
        .show()
        .text(markdownBadge(url));
      return false;
    });

    $('#rst-badge-toggle').on('click', function () {
      var url = updateUrl();
      $('#badge-snippet')
        .show()
        .text(rstBadge(url));
      return false;
    });

    $('#basic-url-toggle').on('click', function () {
      var url = updateUrl();
      $('#badge-snippet')
        .show()
        .text(url);
      return false;
    });

    log.open(document.getElementById('log'), false);
    $(window).resize(function() {
        log.fit();
    });

    $('#toggle-logs').click(function() {
        var $panelBody = $('#log-container .panel-body');
        if ($panelBody.hasClass('hidden')) {
            $('#toggle-logs button').text('hide');
            $panelBody.removeClass('hidden');
            logsVisible = true;
        } else {
            $('#toggle-logs button').text('show');
            $panelBody.addClass('hidden');
            logsVisible = false;
        }

        return false;
    });

    $('#build-form').submit(function() {
        var repo = $('#repository').val().trim();
        var ref =  $('#ref').val().trim();
        repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
        // trim trailing or leading '/' on repo
        repo = repo.replace(/(^\/)|(\/?$)/g, '');
        var image = new Image('gh', repo + '/' + ref);

        var url = updateUrl();
        // add fixed build URL to window history so that reload with refill the form
        if (window.location.href !== url) {
          window.history.pushState({}, '', url);
        }

        $('#build-progress .progress-bar').addClass('hidden');
        log.clear();

        $('.on-build').removeClass('hidden');

        image.onStateChange('*', function(oldState, newState, data) {
            if (data.message !== undefined) {
                log.fit();
                log.write(data.message);
            } else {
                console.log(data);
            }
        });

        image.onStateChange('waiting', function(oldState, newState, data) {
            $('#phase-waiting').removeClass('hidden');
        });

        image.onStateChange('building', function(oldState, newState, data) {
            $('#phase-building').removeClass('hidden');
        });

        image.onStateChange('pushing', function(oldState, newState, data) {
            $('#phase-pushing').removeClass('hidden');
        });
        image.onStateChange('failed', function(oldState, newState, data) {
            failed = true;
            $('#build-progress .progress-bar').addClass('hidden');
            $('#phase-failed').removeClass('hidden');
            // If we fail for any reason, we will show logs!
            if (!logsVisible) {
                $('#toggle-logs').click();
            }
            image.close();
        });

        image.onStateChange('built', function(oldState, newState, data) {
            if (oldState === null) {
                $('#phase-already-built').removeClass('hidden');
                $('#phase-launching').removeClass('hidden');
            }
        });

        image.onStateChange('ready', function(oldState, newState, data) {
            image.close();
            // fetch runtime params!
            var filepath = $("#filepath").val().trim();
            image.launch(data.url, data.token, filepath);
        });

        image.fetch();
        return false;
    });

    if (window.submitBuild) {
        $('#build-form').submit();
    }
});
