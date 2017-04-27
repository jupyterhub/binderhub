$(function(){

    $('#build-form').submit(function() {
        var repo =  ($('#repo').val());
        var url = '/build/github/' + repo + '/master';
        var source = new EventSource(url);

        source.addEventListener('message', function(e){
            var data = JSON.parse(e.data);
            $('#log').append($('<li>').text(data.payload));
            if (data.kind == 'pod.phasechange') {
                if (data.payload == 'Succeeded' || data.payload == 'Failed') {
                    source.close()
                }
            }
        }, false)
        return false;
    })
})
