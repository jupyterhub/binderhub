$(function(){
    var log = new Terminal({
        convertEol: true,
        disableStdin: true
    });
    log.open(document.getElementById('log'));
    log.fit();

    $('#build-form').submit(function() {
        var repo =  ($('#repository').val());
        repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
        var url = '/build/github/' + repo + '/master';
        var source = new EventSource(url);

        log.clear();

        source.addEventListener('message', function(e){
            var data = JSON.parse(e.data);
            log.writeln(JSON.stringify(data));
            if (data.kind == 'pod.phasechange' && data.payload == 'Failed') {
                source.close();
            }
            if (data.kind == 'buildComplete') {
                var url = '/redirect?image=' + data.payload.imageName;
                source.close();
                window.location.href = url;
            }
        }, false);
        return false;
    });
});
