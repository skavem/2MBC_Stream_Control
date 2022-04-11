var text_shown = false; 

function start_ws(){
    ws = new WebSocket('ws://192.168.1.100:8765');

    ws.addEventListener("close", function() {
        setTimeout(function() { start_ws(); }, 1000);
    })
    ws.addEventListener('message', function(event) { 
        message_handler(event); 
    });
}

function message_handler(event){
    input = JSON.parse(event.data);
    console.log(input);

    if (input.hasOwnProperty('hide_verse')) {
        $verse_field.animate([{opacity: 1}, {opacity: 0}], {duration: 1000, fill: "forwards"});
        text_shown = false;
        return;
    }
    if (input.hasOwnProperty('verse')) {
        $verse_field.classList.remove('d-none');
        $song_field.classList.add('d-none');
        $verse_text.textContent = input['verse'];
        $reference_text.textContent = input['ref'];
        if (!text_shown) {
            $verse_field.animate([{opacity: 0}, {opacity: 1}], {duration: 1000, fill: "forwards"});
        }
        text_shown = true;
        return;
    }
    if (input.hasOwnProperty('couplet')) {
        $verse_field.classList.add('d-none');
        $song_field.classList.remove('d-none');
        $song_text.textContent = input['couplet'];
        console.log(input['couplet'])
    }
    if (input.hasOwnProperty('hide_song')) {
        $verse_field.classList.remove('d-none');
        $song_field.classList.add('d-none');
    }
    if (input.hasOwnProperty('song_font_size_change')) {
        $song_text.style.fontSize = input['song_font_size_change']+'em';
        $verse_text.style.fontSize = input['verse_font_size_change']+'em';
    }
}

function on_load_script() { 
    $song_field = document.getElementById('song');
    $song_text = document.getElementById('song_text');
    $verse_field = document.getElementById('verse');
    $verse_text = document.getElementById('verse_text');
    $reference_text = document.getElementById('reference');
    start_ws();
    window.addEventListener("beforeunload", function(){ws.close();}, false);
}