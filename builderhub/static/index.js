// If this file gets over 150 lines of code long, start using a framework
$(function(){
    var log = new Terminal({
        convertEol: true,
        disableStdin: true
    });
    log.open(document.getElementById('log'));
    log.fit();

    $('#build-form').submit(function() {
        var repo = $('#repository').val();
        repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
        var ref =  $('#ref').val()
        var url = '/build/github/' + repo + '/' + ref;
        var source = new EventSource(url);

        $('#log-container').toggleClass('hidden');
        log.fit();
        log.clear();


        source.addEventListener('message', function(e){
            var data = JSON.parse(e.data);
            if (data.message) {
                log.writeln(data.message);
            } else {
                log.writeln(JSON.stringify(data));
            }
            if (data.phase == 'completed') {
                // FIXME: make this proper and secure lol
                var filepath = $('#filepath').val();
                var filepathParts = filepath.split('#');
                if (filepath == '') {
                    filepath = '/tree';
                } else if (filepathParts[0].endsWith('.ipynb')) {
                    filepath = '/notebooks/' + filepath;
                } else {
                    filepath = '/edit/' + filepath;
                }
                var url = '/redirect?image=' + data.imageName + '&default_url=' + filepath;
                source.close();
                window.location.href = url;
            }
        }, false);
        return false;
    });

    if (window.submitBuild) {
        $('#build-form').submit();
    }
});
