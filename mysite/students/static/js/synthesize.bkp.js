const SPEECH_INDIA_TTS = "https://10.210.8.77/tts4/";
const TTS_BHASHINI_API = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
const TTS_API_BHASHINI_PROXY = "https://10.210.8.77/asr/synthesis_bhasini";

var audio = new Audio();
var audio_wait = new Audio();

var isPlaying = false;
// to get service id if language changes
var previous_lang;

var speakerButton = document.getElementById("speakerButton");
const playbackSpeedControl = document.getElementById('playback_speed');
const display_playback_speed = document.getElementById('display_playback_speed');
var playback_speed = 1
const STEP = 0.05;
const MIN = parseFloat(playbackSpeedControl.min);
const MAX = parseFloat(playbackSpeedControl.max);

function synthesize(text, lang = langcode) {
    // console.log("Model : ", service_id_tts)
    if (service_id_tts == "None" && previous_lang != lang) {
        previous_lang = lang;
        getServiceId("tts", lang, text);
    }
    else {
        console.log("TTS: serviceId: ", service_id_tts, lang)
        synthesisAudioProxy(text, service_id_tts, lang);
    }
}

function synthesisAudioProxy(text, serviceIdTTS, lang) {

    text_filename = userID.trim() + "_tts_" + getDateTime() + ".txt"

    const TTSFormData = new FormData();
    TTSFormData.append("language", lang);
    TTSFormData.append("text", text);
    TTSFormData.append("service_id", serviceIdTTS);
    TTSFormData.append("file_name", text_filename);
    // TTSFormData.append("user_id", userID);


    var oReq = new XMLHttpRequest();
    // oReq.open("POST", TTS_API_BHASHINI_PROXY, true);
    oReq.open("POST", synthesize_remote, true);
    oReq.onload = function (oEvent) {
        if (oReq.status == 200) {
            // console.log("TTS Response: ", oReq.response);
            tts_response = oReq.response;
            const obj = JSON.parse(tts_response);

            audio_base_64 = obj.audio
            state = document.getElementById("stop_resume").innerHTML

            if (state == "Resume") {
                audio_wait.src = "data:audio/wav;base64," + audio_base_64;
                audio_wait.load();
                audio_wait.play();
                
                audio_wait.playbackRate = playback_speed
            } else {
                audio.pause();
                audio.src = "data:audio/wav;base64," + audio_base_64;
                audio.load();
                audio.play();
                audio.playbackRate = playback_speed
                isPlaying = true;
                speakerButton.classList.add("speakering");
                speakerButton.style.backgroundColor = 'yellow'
            }
        }
        if (oReq.status === 500) {
            transcribed_text = "not able to synthesis"
            // console.log("Trying our TTS")
            // synthesizeSpeechIndia(text);

        }
        response_wait_audio.pause();
        JsLoadingOverlay.hide();
    };
    console.log("Sending text... ");
    JsLoadingOverlay.show({
        'overlayBackgroundColor': '#ffffff',
        'spinnerIcon': 'ball-beat'
    });
    response_wait_audio.load();
    response_wait_audio.play();

    oReq.send(TTSFormData);
}

function synthesisBhashiniText(text, serviceIdTTS, lang) {

    var postData = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": lang
                    },
                    "serviceId": serviceIdTTS,
                    // "modelId":"6576a17e00d64169e2f8f43d",
                    "gender": "female"
                }
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": text
                }
            ],
            "audio": [
                {
                    "audioContent": null
                }
            ]
        }
    }

    console.log("Sending audio request ...")

    var xhr = new XMLHttpRequest();
    // var SPEECH_INDIA_TTS = TTS_BHASHINI_API;
    xhr.open("POST", TTS_BHASHINI_API, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", "EiVNa6kESRXNBtJ5C2-WPsVsuq8GM92oPKayD3SeqMm4ssTww4KMgapQmdS3kDPD");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log("pause wait message!")
            var json = JSON.parse(xhr.responseText);
            // console.log("ASR Response: ",oReq.response);
            audio_base_64 = json["pipelineResponse"][0]["audio"][0]["audioContent"]

            state = document.getElementById("stop_resume").innerHTML

            if (state == "Resume") {
                audio_wait.src = "data:audio/wav;base64," + audio_base_64;
                audio_wait.load();
                audio_wait.play();
            } else {
                audio.src = "data:audio/wav;base64," + audio_base_64;
                audio.load();
                audio.play();
                isPlaying = true;
                speakerButton.classList.add("speakering");
            }

        }
        if (xhr.status === 500) {
            console.log("no response from tts")
        }
        response_wait_audio.pause();
        JsLoadingOverlay.hide();
    };
    var data = JSON.stringify(postData);
    // console.log(data)
    JsLoadingOverlay.show({
        'overlayBackgroundColor': '#ffffff',
        'spinnerIcon': 'ball-beat'
    });
    response_wait_audio.load();
    response_wait_audio.play();

    xhr.send(data);
}

// for our TTS
function synthesizeSpeechIndia(text) {

    const count = Date.now();
    const lang = "hindi"
    const speed = "1"
    //console.log("Inside sythesis.js : ", text)
    //var selText = document.getElementById("ip").value;

    var params = "Languages=" + lang + "&ex=execute&op=" + text + "&count=" + count + "&speed=" + speed;

    http = new XMLHttpRequest();
    http.open("POST", SPEECH_INDIA_TTS + "synthesis.php", true);

    http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    // http.setRequestHeader("Access-Control-Allow-Origin", "*");
    // http.setRequestHeader("Content-length", params.length);
    // http.setRequestHeader("Connection", "close");


    http.onreadystatechange = function () {
        if (http.readyState == 4) {
            var resTxt = http.responseText;
            var startTxt = resTxt.indexOf("temp/");
            var endTxt = resTxt.indexOf(".mp3", startTxt);
            var spCode = resTxt.substring(startTxt, endTxt);
            //for testing
            // for synthesis
            audio.src = SPEECH_INDIA_TTS + "wav_output/fest_out" + count + ".mp3";
            audio.load();
            audio.play();
            isPlaying = true;


            // document.dispatchEvent(synthesisFinishEvent);
        }
    }
    http.send(params);
}

// for slider
// playbackSpeedControl.addEventListener('input', e => {
//     audio.playbackRate = parseFloat(e.target.value);
//     playback_speed = parseFloat(e.target.value);
//     display_playback_speed.innerHTML = playback_speed;
// });


playbackSpeedControl.addEventListener('input', e => {
    const value = parseFloat(e.target.value);

    // Apply playback speed
    audio.playbackRate = value;

    // Update UI display
    display_playback_speed.innerHTML = value + "x";

    // Accessibility updates
    playbackSpeedControl.setAttribute('aria-valuenow', value);

    // Better readable text for screen readers
    let text;
    if (value === 1) {
        text = "Normal speed";
    } else if (value < 1) {
        text = value + " times slower";
    } else {
        text = value + " times faster";
    }

    playbackSpeedControl.setAttribute('aria-valuetext', text);
});


//for keys
// function setPlaybackSpeedRate(rate) {
//     const rounded = Math.round(rate / STEP) * STEP;
//     playback_speed = Math.min(MAX, Math.max(MIN, Number(rounded.toFixed(2))));
//     audio.playbackRate = playback_speed;
//     playbackSpeedControl.value = playback_speed;
//     display_playback_speed.innerHTML = playback_speed;
// }

function setPlaybackSpeedRate(rate) {
    const rounded = Math.round(rate / STEP) * STEP;

    playback_speed = Math.min(
        MAX,
        Math.max(MIN, Number(rounded.toFixed(2)))
    );

    // Apply playback speed to audio
    audio.playbackRate = playback_speed;

    // Sync slider position
    playbackSpeedControl.value = playback_speed;

    // Update UI display (with x)
    display_playback_speed.innerHTML = playback_speed + "x";

    // Accessibility updates
    playbackSpeedControl.setAttribute('aria-valuenow', playback_speed);

    // Generate meaningful speech text
    let text;
    if (playback_speed === 1) {
        text = nrml_speed ;
    } else if (playback_speed < 1) {
        text = playback_speed + " " + slow_speed;
    } else {
        text = playback_speed + " " + fast_speed;
    }

    playbackSpeedControl.setAttribute('aria-valuetext', text);
}
  