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
        JSON.parse(message['songs'], (number, text) => {
            if (text) $songs.append($('<option>', {value: number, text: number + ': ' + text}));
        });
        $songs.prop('selectedIndex', 0);
        get_couplets();
    }

    /// If couplets
    if(message.hasOwnProperty("couplets")) {
        let $couplets = $('#couplet');
        $couplets.empty();
        message['couplets'].forEach(couplet => {
            if (couplet) $couplets.append($('<option>', {value: couplet[0], text: couplet[1]}));
        });
        $couplets.prop('selectedIndex', 0);
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

    /// Close socket before closing
    $(window).on("beforeunload", function(){
        ws.close();
    });
}

/// On page ready (loaded) run
$(document).ready(on_load_script);