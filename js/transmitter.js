/// Incoming messages
function message_handler(event){
    message = JSON.parse(event.data);
    console.log(message);
    
    /// If verse
    if(message.hasOwnProperty("books")) {
        var books = $('#book');
        JSON.parse(message["books"], (abb, full_name) => {
            if (abb) books.append($('<option>', { value: abb, text:full_name }));
        });
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
                text: verse[3]+" "+verse[2]+":"+verse[1]+" "+verse[0], class: 'text-wrap'
            }));
        }
    }

    /// If songs
    if(message.hasOwnProperty("songs")) {
        let $songs = $('#song');
        $songs.empty();
        JSON.parse(message['songs']).forEach(song_list => {
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
                $couplets.append($('<option>', {value: couplet[0]})
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
        alert_field.text(message["error"]);
        alert_field.show();
        setTimeout(function() { alert_field.hide(); }, 4000);
    }
}

/// Creating Web Socket
function create_websocket() {
    ws = new WebSocket('ws://localhost:8765');

    ws.addEventListener("close", function() {
        alert_field.text("Нет соединения с хостом");
        alert_field.show();
        setTimeout(function() { create_websocket(); }, 1000);
    })
    ws.addEventListener('open', function () { 
        ws.send("Transmitter"); 
        alert_field.hide();
    });
    ws.addEventListener('message', function(event) { 
        message_handler(event); 
    });
}

/// Send data to host
function send_data(form) {
    var unindexed_array = form.serializeArray();
    var to_json = {};

    $.map(unindexed_array, function(n, i) {
        to_json[n['name']] = n['value']
    });
    
    ws.send(JSON.stringify(to_json));
}

/// Change chapters for book
function get_chapters() {
    ws.send(JSON.stringify({"get_chapters": book_field.prop('value')}));
}

/// Change verses for chapter
function get_verses(){
    ws.send(JSON.stringify(
        { "get_verses": { "book": book_field.prop('value'),
                          "ch": chapter_field.prop('value') } 
        }
    ));
}

/// Change song for couplets
function get_couplets() {
    ws.send(JSON.stringify({"get_couplets": $song_field.prop('value')}));
}

/// On body loaded
function on_load_script(){        
    alert_field = $("#alert-danger");
    alert_field.hide();

    /// Web Socket
    create_websocket();

    /// Form
    Bible_send = $("#Bible_send");
    Bible_send.on("submit", function (event) {
        event.preventDefault();
        send_data(Bible_send);
    } );
    Bible_send.on("reset", function (event) {
        event.preventDefault();
        ws.send(JSON.stringify({"hide_verse": true}));
    } );

    /// Bible navigation
    book_field = $("#book");
    book_field.on("change", get_chapters);

    chapter_field = $("#ch");
    chapter_field.on("change", get_verses);

    verses_field = $("#vr");
    verses_field.on("dblclick", function() {
        send_data(Bible_send);
    });

    /// Bible search
    $('#Bible_search').on('submit', function (event) {
        event.preventDefault();
        ws.send(JSON.stringify({'find_verse': $('#search_str').prop('value')}));
    });
    $('#search_str').on('input', function() {
        ws.send(JSON.stringify({'find_verse': $('#search_str').prop('value')}));
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
        send_data($Songs_send);
    });
    $Songs_send.on('reset', function(event) {
        event.preventDefault();
        ws.send(JSON.stringify({"hide_song": true}));
    });

    $song_field = $('#song');
    $song_field.on('change', get_couplets);

    $couplet_field = $('#couplet');
    $couplet_field.on('dblclick', function () {
        send_data($Songs_send); 
    });

    /// Song search
    $Song_search = $('#Song_search');
    $Song_search.on('submit', function(event) {
        event.preventDefault();
        send_data($Song_search);
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
        send_data($Couplet_edit);
        setTimeout(get_couplets, 200);
        bootstrap.Modal.getInstance(document.getElementById('couplet_edit_modal')).hide()
    });

    $couplet_delete = $('#couplet_delete');
    $couplet_delete.on('click', function () {
        if(confirm('Удалить куплет?')) {
            ws.send(JSON.stringify({'remove_couplet_id': $couplet_field.val()[0], 'remove_from_song_id': $song_field.val()[0]}));
            setTimeout(get_couplets, 200);
        } else {
            return;
        }
    })

    $couplet_up = $('#couplet_up');
    $couplet_up.on('click', function () {
        ws.send(JSON.stringify({'couplet_move_up': $couplet_field.val()[0], 'move_from_song_id': $song_field.val()[0]}))
        setTimeout(get_couplets, 200);
    })
    $couplet_down = $('#couplet_down');
    $couplet_down.on('click', function () {
        ws.send(JSON.stringify({'couplet_move_down': $couplet_field.val()[0], 'move_from_song_id': $song_field.val()[0]}))
        setTimeout(get_couplets, 200);
    })

    /// Close socket before closing
    $(window).on("beforeunload", function(){
        ws.close();
    });
}

/// On page ready (loaded) run
$(document).ready(on_load_script);