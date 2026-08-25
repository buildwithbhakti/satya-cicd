var response_wait_audio = new Audio();
response_wait_audio.src = wait_msg_mp3
response_wait_audio.loop = true;
response_wait_audio.volume = 0.3;

// response_wait_audio.play();

// function StopResume() {
//     // console.log("isRecording", isRecording, "isPlaying", isPlaying);

//     audio_wait.pause();

//     if (isPlaying == false && isRecording == false) {
//         return;
//     }

//     state = document.getElementById("stop_resume").innerHTML
//     if (state == "Pause") {

//         logger.log({
//             mode: 'keyboard',
//             type: 'command',
//             activity: 'paused',
//             function_name: "StopResume()"
//         });

//         console.log("Paused");
//         if (isPlaying == true) {
//             audio.pause()
//             speakerButton.classList.remove('speakering');
//         }
//         if (isRecording == true) {
//             pauseResumeRecording()
//         }
//         document.getElementById("stop_resume").innerHTML = "Resume"
//         synthesize("we are waiting");
//         // synthesize(translate.waitingMsg);

//     }
//     if (state == "Resume") {
//         console.log("Resumed");

//         logger.log({
//             mode: 'keyboard',
//             type: 'command',
//             activity: 'resumed',
//             function_name: "StopResume()"
//         });

//         if (isPlaying == true) {
//             audio.play()
//             speakerButton.classList.add('speakering');
//         }
//         if (isRecording == true) {
//             pauseResumeRecording()
//         }

//         document.getElementById("stop_resume").innerHTML = "Pause"
//     }
// }


function StopResume() {
    audio_wait.pause();

    const button = document.getElementById("stop_resume");
    const currentState = button.dataset.state; // 'pause' or 'resume'
    console.log("STOP RESUME : ", currentState)

    // Early return if nothing is active
    if (currentState === "halt") {
        handleResume(button);
    } else if (!isPlaying && !isRecording) {
        return;
    }
    
    if (currentState === "pause") {
        handlePause(button);
    } else if (currentState === "resume") {
        handleResume(button);
    }
}

let lastPlayedQuestion = null; // Track which question's audio is currently loaded

function handlePause(button) {
    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'paused',
        function_name: "StopResume()"
    });

    console.log("Paused");

    // Pause audio playback (keeps buffer intact)
    if (isPlaying) {
        audio.pause();
        speakerButton.classList.remove('speakering');
    }

    // Pause recording
    if (isRecording) {
        pauseResumeRecording();
    }

    // Update button state
    button.dataset.state = "resume";
    // button.textContent = button.dataset.resumeText;
    updateButtonUI(button, "resume"); 


    synthesize("we are waiting");
}

function handleResume(button) {
    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'resumed',
        function_name: "StopResume()"
    });

    console.log("Resumed");

    const currentQno = (typeof current !== "undefined") ? current + 1 : null;
    
    
    // Check if we're on the same question
    if (lastPlayedQuestion === currentQno && audio.src) {
        // Same question - just resume the paused audio
        console.log("Resuming same question audio from", audio.currentTime);

        if (isPlaying || audio.paused) {
            audio.play();
            speakerButton.classList.add('speakering');
        }
    } else {
        // Different question or no audio loaded - read new question
        console.log("Playing new question", currentQno);
        clearAllAudio();
        readQuestion(currentQno);
        lastPlayedQuestion = currentQno;
    }

    // Resume recording if it was active
    if (isRecording) {
        pauseResumeRecording();
    }

    // Update button state
    button.dataset.state = "pause";
    // button.textContent = button.dataset.pauseText;
    updateButtonUI(button, "pause"); // ← Call here

}

function updateButtonUI(button, state) {
    const pauseIcon = document.getElementById('pause-icon');
    const resumeIcon = document.getElementById('resume-icon');

    if (state === 'pause') {
        // Show pause icon/text
        if (pauseIcon && resumeIcon) {
            pauseIcon.style.display = 'block';
            resumeIcon.style.display = 'none';
        } else {
            // Fallback to text if icons don't exist
            button.textContent = button.dataset.pauseText;
        }
        button.setAttribute('aria-label', button.dataset.pauseText);
    } else {
        // Show resume/play icon/text
        if (pauseIcon && resumeIcon) {
            pauseIcon.style.display = 'none';
            resumeIcon.style.display = 'block';
        } else {
            // Fallback to text if icons don't exist
            button.textContent = button.dataset.resumeText;
        }
        button.setAttribute('aria-label', button.dataset.resumeText);
    }
}

function clearAllAudio() {
    // Stop and clear main audio
    if (window.audio) {
        window.audio.pause();
        window.audio.currentTime = 0;
        window.audio.src = '';
        window.audio.load();
    }

    // Update state
    window.isPlaying = false;

    // Update UI
    if (window.speakerButton) {
        window.speakerButton.classList.remove('speakering');
        window.speakerButton.style.backgroundColor = '';
    }

    // Abort any pending TTS requests
    if (typeof TTSState !== 'undefined' && TTSState.isLoading) {
        TTSState.abort();
    }

    // Reset last played question tracker
    lastPlayedQuestion = null;
}

function interrupt() {

    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'interrupted',
        function_name: "interrupt()"
    });

    console.log("interrupted")
    if (isPlaying == true) {
        audio.pause();
        isPlaying == false
        speakerButton.classList.remove('speakering');
    }
    if (isRecording == true) {
        recorder.mic.stop();
        window.stop();
        isRecording = false;
        micButton.classList.remove('recording');

    }
    synthesize("speak the command", "en");
    state = document.getElementById("stop_resume").innerHTML

    if (state == "Resume") {
        audio_wait.onended = function (event) {
            isPlaying = false;
            speakerButton.classList.remove('speakering');
            console.log("question no. reasume", resume_question)
            StopResume()
            if (resume_question != -1)
                navigateExam(resume_question, 0);
            else
                navigateExam(1, 0);
        }

    } else {
        audio.onended = function (event) {
            isPlaying = false;
            speakerButton.classList.remove('speakering');
            console.log("question no. reasume", resume_question)

            if (resume_question != -1)
                navigateExam(resume_question, 0);
            else
                navigateExam(1, 0);
        }
    }
}


function play_wait_msg() {
    console.log("play wait message!")
    response_wait_audio.src = wait_msg_mp3;
    response_wait_audio.load();
    response_wait_audio.play();
}

// keymappings
document.addEventListener('keydown', function (event) {
    // play pause on space bar press
    // Check if the space bar (key code 32) is pressed
    if (event.ctrlKey === true && event.code === 'Space') {
        event.preventDefault(); // Prevent the default action (scrolling)
        console.log('Space pressed')
        StopResume();
    }

    if (event.ctrlKey === true && event.code === 'Period') {
        event.preventDefault();
        console.log('increase playback speed')
        setPlaybackSpeedRate(audio.playbackRate + STEP);
    }
    if (event.ctrlKey === true && event.code === 'Comma') {
        event.preventDefault();
        setPlaybackSpeedRate(audio.playbackRate - STEP);
        console.log('descrease playback speed')
    }
});


// helper function
function getDateTime() {
    var currentdate = new Date();
    var datetime = currentdate.getDate() + "-" +
        (currentdate.getMonth() + 1) + "-" +
        currentdate.getFullYear() + "_" +
        currentdate.getHours() + ":" +
        currentdate.getMinutes() + ":" +
        currentdate.getSeconds();
    return datetime;
}

// tts
async function speak(text) {    
    await new Promise((resolve, reject) => {
        synthesize(text); // your existing function that plays audio and sets `audio`
        audio.onended = () => {
            isPlaying = false;
            speakerButton.classList.remove('speakering');
            speakerButton.style.backgroundColor = ''
            resolve();
        };
        audio.onerror = e => {
            console.log("error::")
            reject(e);
        }
    });
}


// asr
async function getReply(opts = {}) {
    // start mic and wait for transcription event once
    return await new Promise((resolve, reject) => {
        try {
            micButtonClicked(opts);
        } catch (e) {
            return reject(e);
        }

        const handler = () => {
            document.removeEventListener(eventCount, handler);
            // for descriptive answer do not remove anything form text.
            if ('color' in opts)
                speechResult = transcribed_text;
            else
                speechResult = transcribed_text.replace(/[.,]/g, '').toLowerCase().trim();

            console.log("speech received: ", speechResult)
            resolve(speechResult);

            // for take test page to enable and disable navigation buttons when speaking
            if (typeof current !== "undefined"){
                dots.forEach(button => button.disabled = false);
                nextBtn.disabled = false;
                prevBtn.disabled = false;
            }

        };
        document.addEventListener(eventCount, handler);

        if (typeof current !== "undefined"){
        dots.forEach(button => button.disabled = true);
        nextBtn.disabled = true;
        prevBtn.disabled = true
        }

        handler.onerror = e => {
            document.removeEventListener(eventCount, handler);
            reject(e);
        }

    });
}

// both asr and tts
async function speakAndGetReply(text, opts = {}) {
    await speak(text)
    return await getReply(opts);

}

// to get asr or tts service id from db
function getServiceId(task, lang, text, selected = true) {
    $.ajax({
        url: speech_models_url,
        type: 'POST',
        dataType: "json",
        contentType: "application/json; charset=utf-8",

        data: JSON.stringify({
            language: lang,
            task: task,
            selected: selected
        }),
        beforeSend: function () {},
        success: function (data, textStatus) {
            // console.log(data);
            if (data != null) {
                if (task == "asr") {
                    serviceId_ASR = data.service_id;
                }
                if (task == "tts") {
                    service_id_tts = data.service_id;
                    synthesisAudioProxy(text, service_id_tts, lang);
                }
                console.log(task, " serviceId fetched: ", data.service_id, lang)

            } else {
                console.log("Not able to get Service ID, check DB", service_id_tts)
            }
            // console.log("Response : ", data, "\n Status:", textStatus)
        },
        error: function (errorMessage) {
            console.log('Error ' + errorMessage);
        }
    });
}



function showPlayDialog() {
    
    if (typeof audioModal !== 'undefined' && audioModal) {
        audioModal.showModal();
        const playAudioBtn = document.getElementById("playAudioBtn");
        playAudioBtn.onclick = function() {
            audioModal.close();
            // const button = document.getElementById("stop_resume");
            window.isPlaying = true;
            window.audio.play();
            window.speakerButton?.classList.add('speakering');
            if (window.speakerButton) window.speakerButton.style.backgroundColor = 'yellow';
        }
    } else {
        console.warn('audioModal is not defined');
    }
    

}


window.addEventListener("load", async () => {
        try {
            await window.response_wait_audio.play();
        } catch (err) {
            showPlayDialog();
        } finally {
            window.response_wait_audio.pause()
        }
});