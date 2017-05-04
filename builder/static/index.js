$(function(){

    $('#build-form').submit(function() {
        var repo =  ($('#repository').val());
        repo = repo.replace(/^(https?:\/\/)?github.com\//, '');
        var url = '/build/github/' + repo + '/master';
        $('#log').empty();
        var source = new EventSource(url);

        source.addEventListener('message', function(e){
            var data = JSON.parse(e.data);
            $('#log').append($('<li>').text(data.payload));
            $('#log').animate({scrollTop: $('#log')[0].scrollHeight}, 1000);
            if (data.kind == 'pod.phasechange') {
                if (data.payload == 'Deleted') {
                    source.close()
                }
            }
        }, false)
        return false;
    })
})
