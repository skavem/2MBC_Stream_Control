/// Incoming messages
function message_handler(event){
    message = JSON.parse(event.data);
    console.log(message);
    
    /// If verse
    if(message.hasOwnProperty('books')) {
        var books = $('#book');
        for ([abb, full_name] of Object.entries(message['books'])) {
            if (abb) books.append($('<option>', { value: abb, text:full_name }));
        };
        books.prop('selectedIndex', 0);
        get_chapters();
    }

    /// If number of chapters
    if(message.hasOwnProperty("number_of_chapters")) {
        let chapters = $('#ch');
        chapters.empty();
        for (let index = 1; index <= message['number_of_chapters']; index++) {
            chapters.append($('<option>', { value: index, text: index }));
        }
        chapters.prop('selectedIndex', 0);
        get_verses();
    }

    /// If number of verses
    if(message.hasOwnProperty("number_of_verses")) {
        let verses = $('#vr');
        verses.empty();
        for (let index = 1; index <= message['number_of_verses']; index++) {
            verses.append($('<option>', { value: index, text: index+": "+message['verses'][index] }))
        }
    }

    /// If search
    if(message.hasOwnProperty('search_result')) {
        let found_vrs = $('#found_vrs'); 
        let verses = message['search_result'];
        found_vrs.empty();
        for (let i = 0; i < verses.length; i++) {
            verse = verses[i];
            found_vrs.append($('<option>', {
                value: verse[3]+";"+verse[2]+";"+verse[1], 
                text: verse[3]+" "+verse[2]+":"+verse[1]+" "+verse[0], 
                class: 'text-wrap'
            }));
        }
    }

    /// If songs
    if(message.hasOwnProperty("songs")) {
        let $songs = $('#song');
        $songs.empty();
        message['songs'].forEach(song_list => {
            let id = song_list[0];
            let number = song_list[1];
            let text = song_list[2];
            if (text) $songs.append($('<option>', {value: id, text: number + ': ' + text}))
        });
        $songs.prop('selectedIndex', 0);
        get_couplets();
    }

    /// If couplets
    if(message.hasOwnProperty("couplets")) {
        let $couplets = $('#couplet');
        $couplets.empty();
        message['couplets'].forEach(couplet => {
            if (couplet) 
                $couplets.append($('<option>', {value: couplet[0], class: 'text-wrap'})
                    .append([
                        $('<span>', {text: couplet[1], class: 'name'}),
                        $('<span>', {text: ': '}),
                        $('<span>', {text: couplet[2], class: 'text'})
                    ]));
        });
        $couplets.prop('selectedIndex', 0);
    }

    if (message.hasOwnProperty('found_song_id')) {
        $song_field.find(':selected').prop('selected', false);
        $song_field.find(`option[value=${message['found_song_id']}]`).prop('selected', true).change();
        setTimeout(() => {
            $song_field.find(':selected')[0].scrollIntoView();
        }, 100);
    }

    /// If error
    if(message.hasOwnProperty("error")) {
        console.log("[Error]: " + message["error"]);
        $alert_field.text(message["error"]);
        $alert_field.show();
        setTimeout(function() { $alert_field.hide(); }, 4000);
    }
}

/// Creating Web Socket
function create_websocket(ws_ip = '192.168.1.100', ws_port = 8765) {
    ws = new WebSocket('ws://' + ws_ip + ':' + ws_port);

    ws.addEventListener("close", function() {
        $alert_field.text("Нет соединения с хостом");
        $alert_field.show();
        if (!ws_full_close) setTimeout(function() { create_websocket(); }, 1000);
        ws_full_close = false;
    });
    ws.addEventListener('open', function () { 
        ws.send("Transmitter"); 
        $alert_field.hide();
    });
    ws.addEventListener('message', function(event) { 
        message_handler(event); 
    });
}

/// Send data to host
function form_to_dict(form) {
    var unindexed_array = form.serializeArray();
    var ret_val = {};

    $.map(unindexed_array, function(n, i) {
        ret_val[n['name']] = n['value']
    });
    
    return ret_val;
}

function send_data(type, object, data) {
    var json_data =  JSON.stringify({'type': type, 'object': object, 'data': data})
    ws.send(json_data);
}

/// Change chapters for book
function get_chapters() {
    send_data(type='get', object='book', data={'book_id': book_field.prop('value')});
}

/// Change verses for chapter
function get_verses(){
    send_data(type='get', object='chapter', data=
    { 
        'book_id': book_field.prop('value'),
        'ch_id': chapter_field.prop('value') 
    }
    );
}

/// Change song for couplets
function get_couplets() {    
    send_data(type='get', object='song', data={'song_id': $song_field.prop('value')});
}

/// On body loaded
function on_load_script(){        
    $alert_field = $('#alert-danger');
    $alert_field.hide();

    ws_full_close = false;

    /// Web Socket
    create_websocket();

    /// Form
    Bible_send = $("#Bible_send");
    Bible_send.on("submit", function (event) {
        event.preventDefault();
        var form_data = form_to_dict(Bible_send);
        send_data(type='send', object='verse', data=form_data);
    } );
    Bible_send.on("reset", function (event) {
        event.preventDefault();
        send_data(type='send', object='reciever', data={'hide_verse': true})
    } );

    /// Bible navigation
    book_field = $("#book");
    book_field.on("change", get_chapters);

    chapter_field = $("#ch");
    chapter_field.on("change", get_verses);

    verses_field = $("#vr");
    verses_field.on("dblclick", function() {
        var form_data = form_to_dict(Bible_send);
        send_data(type='send', object='verse', data=form_data);
    });

    /// Bible search
    $('#Bible_search').on('submit', function (event) {
        event.preventDefault();
        send_data(type='get', object='verse', data={'verse_search_srt': $('#search_str').prop('value')});
    });
    $('#search_str').on('input', function() {
        send_data(type='get', object='verse', data={'verse_search_srt': $('#search_str').prop('value')});
    })

    $('#found_vrs').on('dblclick', function () {
        option_array = $('#found_vrs').val()[0].split(';');
        $('#book').val(option_array[0]).change();
        setTimeout(function() { $('#ch').val(option_array[1]).change(); }, 100);
        setTimeout(function() { $('#vr').val(option_array[2]).change(); }, 400);
    });

    /// Songs
    $Songs_send = $('#Songs_send');
    $Songs_send.on('submit', function(event) {
        event.preventDefault();
        var form_data = form_to_dict($Songs_send);
        send_data(type='send', object='couplet', data=form_data);
    });
    $Songs_send.on('reset', function(event) {
        event.preventDefault();
        send_data(type='send', object='reciever', data={'hide_song': true})
    });

    $song_field = $('#song');
    $song_field.on('change', get_couplets);

    $couplet_field = $('#couplet');
    $couplet_field.on('dblclick', function () {
        var form_data = form_to_dict($Songs_send);
        send_data(type='send', object='couplet', data=form_data);
    });

    /// Song search
    $Song_search = $('#Song_search');
    $Song_search.on('submit', function(event) {
        event.preventDefault();
        var form_data = form_to_dict($Song_search);
        send_data(type='get', object='song', data=form_data);
    })

    /// Couplet editing modal
    $('#couplet_edit_modal').on('show.bs.modal', function(event) {
        let modal_call_type = event.relatedTarget.getAttribute('data-bs-call-type');
        let $selectedCouplet = $('#couplet option:selected');

        $('#couplet_id_input').val($selectedCouplet.val());

        $('#couplet_edit_type_input').val(modal_call_type);

        $('#couplet_new_name').val((modal_call_type === 'new') ? '' : $selectedCouplet.find('span.name').text());
        $('#couplet_new_text').val((modal_call_type === 'new') ? '' : $selectedCouplet.find('span.text').text());
    })

    /// Couplet editing
    $Couplet_edit = $('#Couplet_edit');
    $('#save_couplet_edit').on('click', function () {        
        var form_data = form_to_dict($Couplet_edit);
        send_data(type='edit', object='couplet', data=form_data);

        setTimeout(get_couplets, 200);

        bootstrap.Modal.getInstance(document.getElementById('couplet_edit_modal')).hide()
    });

    $couplet_delete = $('#couplet_delete');
    $couplet_delete.on('click', function () {
        if(confirm('Удалить куплет?')) {
            send_data(type='delete', object='couplet', data={
                'couplet_id': $couplet_field.val(), 
                'song_id': $song_field.val()
            });
            setTimeout(get_couplets, 200);
        } else {
            return;
        }
    })

    $couplet_up = $('#couplet_up');
    $couplet_up.on('click', function () {
        send_data(type='edit', object='couplet', data={'edit_type': 'move_up', 'couplet_id':  $couplet_field.val(), 'song_id': $song_field.val()});
        setTimeout(get_couplets, 200);
    })
    $couplet_down = $('#couplet_down');
    $couplet_down.on('click', function () {
        send_data(type='edit', object='couplet', data={'edit_type': 'move_down', 'couplet_id':  $couplet_field.val(), 'song_id': $song_field.val()});
        setTimeout(get_couplets, 200);
    })

    /// Settings modal
    $('#save_settings').on('click', function () {
        ws_full_close = true;
        ws.close();
        create_websocket(ws_ip=$('#ws_ip').val(), ws_port=$('#ws_port').val());
        bootstrap.Modal.getOrCreateInstance(document.getElementById('settings_modal')).hide();
    })

    /// Font settings modal
    $song_font_size = $('#song_font_size');
    $('#song_font_size_plus').on('click', () => {
        $song_font_size.val(parseFloat($song_font_size.val()) + 0.5);
    });
    $('#song_font_size_minus').on('click', () => {
        $song_font_size.val(parseFloat($song_font_size.val()) - 0.5);
    });
    $('#song_font_size_reset').on('click', () => {
        $song_font_size.val(5);
    });
    
    $verse_font_size = $('#verse_font_size');
    $('#verse_font_size_plus').on('click', () => {
        $verse_font_size.val(parseFloat($verse_font_size.val()) + 0.5);
    });
    $('#verse_font_size_minus').on('click', () => {
        $verse_font_size.val(parseFloat($verse_font_size.val()) - 0.5);
    });
    $('#verse_font_size_reset').on('click', () => {
        $verse_font_size.val(4);
    });
    
    $('#save_font').on('click', () => {
        send_data(type='send', object='reciever', data={
            'song_font_size_change': parseFloat($song_font_size.val()), 
            'verse_font_size_change': parseFloat($verse_font_size.val()) 
        })
    })


    /// Close socket before closing
    $(window).on("beforeunload", function(){
        ws_full_close = true;
        ws.close();
    });
}

/// On page ready (loaded) run
$(document).ready(on_load_script);