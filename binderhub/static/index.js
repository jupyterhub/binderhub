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

Image.prototype.fetch = function() {
    var apiUrl = '/build/' + this.provider + '/' + this.spec;
    this.eventSource = new EventSource(apiUrl);
    var that = this;
    this.eventSource.addEventListener('message', function(event) {
        var data = JSON.parse(event.data);
        // FIXME: Rename 'phase' to 'state' upstream
        // FIXME: fix case of phase/state upstream
        var state = data.phase.toLowerCase();
        if (that.callbacks[state] !== undefined) {
            for(var i = 0; i < that.callbacks[state].length; i++) {
                that.callbacks[state][i](that.state, state, data);
            }
        }
        if (that.callbacks['*'] !== undefined) {
            for(var i = 0; i < that.callbacks['*'].length; i++) {
                that.callbacks['*'][i](that.state, state, data);
            }
        }

        // FIXME: Make sure that this is a valid state transition!
        that.state = state;
    });
};

Image.prototype.close = function() {
    if (this.eventSource !== undefined) {
        this.eventSource.close();
    }
};

Image.prototype.launch = function(runtimeParameters) {
    var url = '/run?' + $.param(runtimeParameters);
    window.location.href = url;
};

$(function(){
    var failed = false;
    var logsVisible = false;
    var log = new Terminal({
        convertEol: true,
        disableStdin: true
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
        var repo = $('#repository').val();
        var ref =  $('#ref').val();
        repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
        var image = new Image('gh', repo + '/' + ref);

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
            image.close();
            image.launch({
                image: data.imageName
            });
        });

        image.fetch();
        return false;
    });

    if (window.submitBuild) {
        $('#build-form').submit();
    }
});
