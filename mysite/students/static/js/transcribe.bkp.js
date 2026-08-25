// ORG_SRC : https://github.com/muaz-khan/RecordRTC/tree/master/simple-demos
// GUI SRC : https://github.com/addpipe/simple-recorderjs-demo

const ASR_API = "https://10.210.8.77/asr/recognize";
const ASR_API_BHASHINI_PROXY = "https://10.210.8.77/asr/recogonize_bhasini";
const AUDIO_API = "https://10.210.8.77/asr/save-audio";

const ASR_BHASHINI_API = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline";

// use graph name "graph_blind_exam" for our asr , "bhashini_asr" for direct request
var graphName = "bhashini_asr_proxy";
var eventCount = 0;
var asrLanguage = "en";

var recorder;
var isRecording = false;
var audio_filename;
var isPaused = false;
var micButton = document.getElementById("micButton");
// var userID = document.getElementById("user_id").innerText;

var transcribed_text = "";
var max_seconds = 2;

var mic_audio_start_stop = new Audio();

// ------ RECORDING FUNCTIONALITY START -----------  

function capturemic(callback) {
    // Check if mediaDevices API is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support audio recording. Please use a modern browser like Chrome, Firefox, or Edge.');
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(function (mic) {
            callback(mic);
        })
        .catch(function (error) {
            let message;

            switch (error.name) {
                case 'NotFoundError':
                case 'DevicesNotFoundError':
                    message = 'No microphone found. Please connect a microphone and try again.';
                    break;

                case 'NotAllowedError':
                case 'PermissionDeniedError':
                    message = 'Microphone access was denied. Please allow microphone permission in your browser settings and try again.';
                    break;

                case 'NotReadableError':
                case 'TrackStartError':
                    message = 'Your microphone is busy or unavailable. Please close other apps using it and try again.';
                    break;

                case 'OverconstrainedError':
                    message = 'Microphone settings are not supported by your device.';
                    break;

                case 'SecurityError':
                    message = 'Microphone access is blocked due to security restrictions. Please use HTTPS or check your browser settings.';
                    break;

                default:
                    message = `Unable to access microphone: ${error.message || 'Unknown error'}. Please check your device and try again.`;
            }

            alert(message);
            console.error('Microphone error:', error);
            synthesize(message, "en");
        });
}

function startRecording() {
    capturemic(function (mic) {
        isRecording = true;

        micButton.classList.add('recording');

        recorder = RecordRTC(mic, {
            type: 'audio',
            desiredSampRate: 16000,
            numberOfAudioChannels: 1,
            recorderType: StereoAudioRecorder,
            disableLogs: true
        });

        recorder.startRecording();


        var stopped_speaking_timeout;
        var speechEvents = hark(mic, {});

        speechEvents.on('speaking', function () {
            if (recorder.getBlob()) return;

            clearTimeout(stopped_speaking_timeout);

            if (recorder.getState() === 'Paused') {
                clearTimeout(stopped_speaking_timeout);
            }

            if (recorder.getState() === 'recording') {
            }
        });

        speechEvents.on('stopped_speaking', function () {
            if (recorder.getBlob()) return;

            if (recorder.getState() === 'Paused') {
                clearTimeout(stopped_speaking_timeout);
            } else {
                stopped_speaking_timeout = setTimeout(function () {
                    stopRecording();
                }, max_seconds * 1000);

                var seconds = max_seconds;
                (function looper() {
                    seconds--;

                    if (isRecording == false) {
                        clearTimeout(stopped_speaking_timeout);
                        return;
                    }
                    if (isPaused) {
                        clearTimeout(stopped_speaking_timeout);
                        // status_text.innerHTML = 'PAUSED!';
                        return;
                    }

                    if (seconds <= 0) {
                        return;
                    }

                    setTimeout(looper, 1000);
                })();
            }
        });
        // release mic on stopRecording
        recorder.mic = mic;
    });
}

function stopRecording() {
    isRecording = false;
    isPaused = false;
    micButton.classList.remove('recording');
    recorder.stopRecording(stopRecordingCallback);
}


function pauseResumeRecording() {
    if (recorder.getState() === 'recording') {
        recorder.pauseRecording();
        // pauseButton.innerHTML = "Resume";
        console.log("Recording Paused");
        micButton.classList.remove('recording');
        // status_text.innerHTML = "PAUSED!";
        isPaused = true;
    } else {
        recorder.resumeRecording();
        // pauseButton.innerHTML = "Pause";
        console.log("Recording Resumed");
        micButton.classList.add('recording');
        isPaused = false;
    }
}

function stopRecordingCallback() {
    var blob = recorder.getBlob();
    recorder.mic.stop();

    mic_audio_start_stop.src = mic_stop_mp3
    mic_audio_start_stop.load();
    mic_audio_start_stop.play();
    micButton.style.backgroundColor = '';


    audio_filename = userID.trim() + "_asr_" + getDateTime() + ".wav"

    if (graphName == "bhashini_asr") {
        // save audio to our server - required for evaluation
        saveAudio(blob, audio_filename);
        transcribeBhashiniAudio(blob, serviceId_ASR);
    }
    else if (graphName == "bhashini_asr_proxy") {
        transcribeAudioProxy(blob, serviceId_ASR, audio_filename);
    }
    else {
        console.log("USING : our asr")
        // transcribeAudio(blob, audio_filename);
        transcribeAudioVosk(blob, audio_filename);
    }
    window.stop();
}

// for spoken question number navigation
function resendToTranscribe() {
    console.log("resending audio..")
    var blob = recorder.getBlob();
    serviceId_ASR = "ai4bharat/whisper-medium-en--gpu--t4";
    audio_filename = userID.trim() + "_asr_" + getDateTime() + ".wav"

    transcribeAudioProxy(blob, serviceId_ASR, audio_filename)
}

// handle mic symbol to start and stop recording
// also work on micButton.click()
function micButtonClicked(opts = {}) {
    console.log("mic clicked... ")
    const {
        lang = 'en',
        server = 'speechindia',
        max_wait_seconds = 2,
        color = 'yellow'
      } = opts;

    if (server == "speechindia") {
        graphName = "graph_blind_exam";

    } else {
        graphName = "bhashini_asr_proxy";

        if (serviceId_ASR == "None")
            getServiceId("asr", lang);
        else
            console.log("ASR: serviceId:", serviceId_ASR, lang)
    }

    micButton.style.backgroundColor = color
    asrLanguage = lang;
    max_seconds = max_wait_seconds

    if (isRecording == false) {
        startRecording();
        mic_audio_start_stop.src = mic_start_mp3
        mic_audio_start_stop.load();
        mic_audio_start_stop.play();

    } else {
        stopRecording();
    }
};

// ------ RECORDING FUNCTIONALITY ENDS ----------- 


/**
 * upload file to the server
 * @param {blob} sound audio
 * @param {string} audio_file_name date_time
 */
function transcribeAudio(sound, audio_file_name) {

    console.log("SIZE : ", sound.size)
    // 10MB limit
    if (sound.size > 10000000) {
        console.log("File limit exceed!")
        return;
    }

    const audioFormData = new FormData();
    audioFormData.append("language", asrLanguage);
    audioFormData.append("audio", sound);
    audioFormData.append("filename", audio_file_name);
    audioFormData.append("graph_name", graphName);

    console.log("GRAPH NAME : ", graphName)

    var oReq = new XMLHttpRequest();
    oReq.open("POST", ASR_API, true);
    oReq.onload = function (oEvent) {
        if (oReq.status == 200) {
            console.log("ASR Response: ", oReq.response);
            asr_response = oReq.response;
            const obj = JSON.parse(asr_response);

            transcribed_text = obj.response
            micButton.disabled = false;

            console.log("Event Object created..", eventCount);
            document.dispatchEvent(new Event(eventCount));
            eventCount++;
        } else {
            micButton.disabled = false;
            console.log("Somethig went wrong!", oReq.response);
        }
        JsLoadingOverlay.hide();
    };
    console.log("Sending audio file... ");
    micButton.disabled = true;
    JsLoadingOverlay.show({
        'overlayBackgroundColor': '#ffffff',
        'spinnerIcon': 'ball-beat'
    });
    oReq.send(audioFormData);
}


function transcribeAudioVosk(sound, audio_file_name) {

    console.log("SIZE : ", sound.size)
    // 1MB limit
    if (sound.size > 1000000) {
        console.log("File limit exceed!")
        return;
    }

    const audioFormData = new FormData();
    audioFormData.append("audio", sound);

    console.log("GRAPH NAME : ", graphName)

    var oReq = new XMLHttpRequest();
    oReq.open("POST", recogonize_local , true);
    oReq.onload = function (oEvent) {
        if (oReq.status == 200) {
            console.log("ASR Response: ", oReq.response);
            asr_response = oReq.response;
            const obj = JSON.parse(asr_response);

            transcribed_text = obj.response
            micButton.disabled = false;

            console.log("Event Object created..", eventCount);
            document.dispatchEvent(new Event(eventCount));
            eventCount++;
        } else {
            micButton.disabled = false;
            console.log("Somethig went wrong!", oReq.response);
        }
        JsLoadingOverlay.hide();
    };
    console.log("Sending audio file... ");
    micButton.disabled = true;
    JsLoadingOverlay.show({
        'overlayBackgroundColor': '#ffffff',
        'spinnerIcon': 'ball-beat'
    });
    oReq.send(audioFormData);
}



function transcribeAudioProxy(blob, serviceId_ASR, audio_filename) {

    const audioFormData = new FormData();
    audioFormData.append("language", asrLanguage);
    audioFormData.append("audio", blob);
    audioFormData.append("service_id", serviceId_ASR);
    audioFormData.append("file_name", audio_filename);

    var oReq = new XMLHttpRequest();
    // oReq.open("POST", ASR_API_BHASHINI_PROXY, true);
    oReq.open("POST", recogonize_remote, true);
    oReq.onload = function (oEvent) {
        if (oReq.status == 200) {
            console.log("ASR Response: ", oReq.response);
            asr_response = oReq.response;
            const obj = JSON.parse(asr_response);

            transcribed_text = obj.text
            micButton.disabled = false;

            console.log("Event Object created..", eventCount);
            document.dispatchEvent(new Event(eventCount));
            eventCount++;
        }
        if (oReq.status === 500) {
            transcribed_text = "error-500"
            micButton.disabled = false;
            document.dispatchEvent(new Event(eventCount));
            eventCount++;
        }
        response_wait_audio.pause();
        JsLoadingOverlay.hide();
    };
    console.log("Sending audio file... ");
    micButton.disabled = true;
    JsLoadingOverlay.show({
        'overlayBackgroundColor': '#ffffff',
        'spinnerIcon': 'ball-beat'
    });
    response_wait_audio.load();
    response_wait_audio.play();
    oReq.send(audioFormData);
}


function transcribeBhashiniAudio(blob, serviceId_ASR) {

    var fileInBase64Format = new FileReader();
    fileInBase64Format.readAsDataURL(blob);
    fileInBase64Format.onloadend = function () {
        var base64data = fileInBase64Format.result;
        base64data = base64data.substr(base64data.indexOf(',') + 1)

        var postData = {

            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": langcode
                        },
                        "serviceId": serviceId_ASR,
                        "preProcessors": ["vad"],
                        "audioFormat": "wav",
                        "samplingRate": 8000
                    }
                }
            ],
            "inputData": {

                "audio": [
                    {
                        "audioContent": base64data
                    }
                ]
            }
        }

        console.log("json sent", postData)

        var xhr = new XMLHttpRequest();
        var url = ASR_BHASHINI_API;
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.setRequestHeader("Authorization", "EiVNa6kESRXNBtJ5C2-WPsVsuq8GM92oPKayD3SeqMm4ssTww4KMgapQmdS3kDPD");
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var json = JSON.parse(xhr.responseText);

                asr_response = json["pipelineResponse"][0]["output"][0]["source"]

                transcribed_text = asr_response
                micButton.disabled = false;

                console.log("Event Object created..", eventCount);

                document.dispatchEvent(new Event(eventCount));
                eventCount++;
            }
            if (xhr.status === 500) {
                transcribed_text = "no response from asr"
                micButton.disabled = false;
                document.dispatchEvent(new Event(eventCount));
                eventCount++;
            }
            JsLoadingOverlay.hide();
        };
        var data = JSON.stringify(postData);
        JsLoadingOverlay.show({
            'overlayBackgroundColor': '#ffffff',
            'spinnerIcon': 'ball-beat'
        });

        xhr.send(data);
    }
}

function saveAudio(blob, audio_filename) {

    const audioFormData = new FormData();
    audioFormData.append("language", "exam_for_blind");
    audioFormData.append("audio", blob);
    audioFormData.append("filename", audio_filename);

    var oReq = new XMLHttpRequest();
    oReq.open("POST", AUDIO_API, true);
    oReq.onload = function (oEvent) {
        if (oReq.status == 200) {
            console.log(" Audio sent")

        } else {
            micButton.disabled = false;
            console.log("Somethig went wrong!", oReq.response);
        }
        JsLoadingOverlay.hide();
    };
    console.log("Sending audio file... ", audio_filename);
    micButton.disabled = true;
    JsLoadingOverlay.show({
        'overlayBackgroundColor': '#ffffff',
        'spinnerIcon': 'ball-beat'
    });
    oReq.send(audioFormData);
}