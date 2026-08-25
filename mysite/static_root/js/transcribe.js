// ORG_SRC : https://github.com/muaz-khan/RecordRTC/tree/master/simple-demos
// GUI SRC : https://github.com/addpipe/simple-recorderjs-demo

// use graph name "graph_blind_exam" for our asr , "bhashini_asr" for direct request
var graphName = "bhashini_asr_proxy";
var eventCount = 0;
var asrLanguage = "en";

var recorder;
var isRecording = false;
var audio_filename = null;
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

function discardRecording() {
    isRecording = false;
    isPaused = false;
    micButton.classList.remove('recording');
    micButton.style.backgroundColor = '';
    recorder.stopRecording(function () {
        recorder.clearRecordedData();
        recorder.mic.stop();
    });

    window.stop();
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

  
    if (graphName == "bhashini_asr_proxy") {
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
    audio_filename = null;

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



// function transcribeAudioVosk(sound, audio_file_name) {

//     console.log("SIZE : ", sound.size)
//     // 1MB limit
//     if (sound.size > 1000000) {
//         console.log("File limit exceed!")
//         return;
//     }

//     const audioFormData = new FormData();
//     audioFormData.append("audio", sound);

//     console.log("GRAPH NAME : ", graphName)

//     var oReq = new XMLHttpRequest();
//     oReq.open("POST", recogonize_local , true);
//     oReq.onload = function (oEvent) {
//         if (oReq.status == 200) {
//             console.log("ASR Response: ", oReq.response);
//             asr_response = oReq.response;
//             const obj = JSON.parse(asr_response);

//             transcribed_text = obj.response
//             micButton.disabled = false;

//             console.log("Event Object created..", eventCount);
//             document.dispatchEvent(new Event(eventCount));
//             eventCount++;
//         } else {
//             micButton.disabled = false;
//             console.log("Somethig went wrong!", oReq.response);
//         }
//         JsLoadingOverlay.hide();
//     };
//     console.log("Sending audio file... ");
//     micButton.disabled = true;
//     JsLoadingOverlay.show({
//         'overlayBackgroundColor': '#ffffff',
//         'spinnerIcon': 'ball-beat'
//     });
//     oReq.send(audioFormData);
// }



// function transcribeAudioProxy(blob, serviceId_ASR, audio_filename) {

//     const audioFormData = new FormData();
//     audioFormData.append("language", asrLanguage);
//     audioFormData.append("audio", blob);
//     audioFormData.append("service_id", serviceId_ASR);
//     audioFormData.append("file_name", audio_filename);

//     var oReq = new XMLHttpRequest();
//     // oReq.open("POST", ASR_API_BHASHINI_PROXY, true);
//     oReq.open("POST", recogonize_remote, true);
//     oReq.onload = function (oEvent) {
//         if (oReq.status == 200) {
//             console.log("ASR Response: ", oReq.response);
//             asr_response = oReq.response;
//             const obj = JSON.parse(asr_response);

//             transcribed_text = obj.text
//             micButton.disabled = false;

//             console.log("Event Object created..", eventCount);
//             document.dispatchEvent(new Event(eventCount));
//             eventCount++;
//         }
//         if (oReq.status === 500) {
//             transcribed_text = "error-500"
//             micButton.disabled = false;
//             document.dispatchEvent(new Event(eventCount));
//             eventCount++;
//         }
//         response_wait_audio.pause();
//         JsLoadingOverlay.hide();
//     };
//     console.log("Sending audio file... ");
//     micButton.disabled = true;
//     JsLoadingOverlay.show({
//         'overlayBackgroundColor': '#ffffff',
//         'spinnerIcon': 'ball-beat'
//     });
//     response_wait_audio.load();
//     response_wait_audio.play();
//     oReq.send(audioFormData);
// }



// ─────────────────────────────────────────────────────────────────────────────
// Robust ASR Proxy — exam-grade reliability
// Covers: transcribeAudioVosk (local) + transcribeAudioProxy (remote/Bhashini)
// Handles: slow networks, disconnects, retries, mic lock, size validation
// ─────────────────────────────────────────────────────────────────────────────

const ASR_CONFIG = {
  TIMEOUT_MS:          20_000,  // audio uploads are larger than TTS text — allow more time
  MAX_RETRIES:         3,
  RETRY_BASE_MS:       800,     // 800 → 1600 → 3200 ms
  SLOW_NET_WARN_MS:    6_000,   // "still working" notice threshold
  MAX_FILE_SIZE_BYTES: 1_000_000, // 1 MB hard limit
  DEDUPE_WINDOW_MS:    500,     // ignore duplicate blobs within this window
  MAX_QUEUE_SIZE:      10,
  DISPATCH_EVENT_KEY:  'asr:transcribed',  // custom event name (see note below)
};

// ─── Singleton ASR state ──────────────────────────────────────────────────────
const ASRState = (() => {
  let _isLoading    = false;
  let _abortCtrl    = null;
  let _lastBlobSize = null;
  let _lastCallAt   = 0;
  const _queue      = [];

  return {
    get isLoading()  { return _isLoading; },
    get queue()      { return _queue; },

    startRequest() {
      _isLoading = true;
      _abortCtrl = new AbortController();
    },
    endRequest() {
      _isLoading = false;
      _abortCtrl = null;
    },
    abort() { _abortCtrl?.abort(); },
    get signal() { return _abortCtrl?.signal; },

    isDuplicate(blob) {
      const now    = Date.now();
      const isDup  = blob.size === _lastBlobSize && (now - _lastCallAt) < ASR_CONFIG.DEDUPE_WINDOW_MS;
      _lastBlobSize = blob.size;
      _lastCallAt   = now;
      return isDup;
    },

    enqueue(item) {
      if (_queue.length >= ASR_CONFIG.MAX_QUEUE_SIZE) _queue.shift();
      _queue.push(item);
    },
    dequeue() { return _queue.shift(); },
  };
})();

// ─── Network monitor (shared pattern from TTS, safe to re-declare if separate file) ──
const ASRNetworkMonitor = (() => {
  let _online = navigator.onLine;
  window.addEventListener('online',  () => { _online = true;  _flushASRQueue(); });
  window.addEventListener('offline', () => { _online = false; _asrShowOfflineBanner(true); });
  return { get isOnline() { return _online; } };
})();

// ─── UI helpers ───────────────────────────────────────────────────────────────
function _asrLockMic(locked) {
  if (window.micButton) window.micButton.disabled = locked;
}

function _asrShowOverlay() {
  if (typeof JsLoadingOverlay !== 'undefined') {
    JsLoadingOverlay.show({ overlayBackgroundColor: '#ffffff', spinnerIcon: 'ball-beat' });
  }
}

function _asrHideOverlay() {
  if (typeof JsLoadingOverlay !== 'undefined') JsLoadingOverlay.hide();
  _asrSetMessage('');
}

function _asrSetMessage(msg) {
  let el = document.getElementById('asr-overlay-msg');
  if (!el) {
    el = document.createElement('div');
    el.id = 'asr-overlay-msg';
    el.style.cssText =
      'position:fixed;top:60px;left:50%;transform:translateX(-50%);' +
      'background:#333;color:#fff;padding:8px 16px;border-radius:6px;' +
      'font-size:14px;z-index:9999;display:none;';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = msg ? 'block' : 'none';
}

function _asrShowOfflineBanner(visible) {
  _asrSetMessage(visible ? '⚠ No internet — microphone queued until reconnected.' : '');
}

function _asrShowRetryMessage(attempt, max) {
  _asrSetMessage(`Network issue — retrying (${attempt}/${max})…`);
}

function _asrShowFinalError(msg) {
  _asrHideOverlay();
  const el = document.getElementById('asr-error-banner') || (() => {
    const d = document.createElement('div');
    d.id = 'asr-error-banner';
    d.style.cssText =
      'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);' +
      'background:#c0392b;color:#fff;padding:12px 20px;border-radius:8px;' +
      'font-size:14px;z-index:9999;cursor:pointer;';
    d.onclick = () => d.remove();
    document.body.appendChild(d);
    return d;
  })();
  el.textContent = msg + '  ✕';
  el.style.display = 'block';
}

// ─── Dispatch transcription result ────────────────────────────────────────────
// Replaces the raw eventCount pattern with a typed CustomEvent carrying the
// transcribed text directly — no shared global needed on the listener side.
// Listeners: document.addEventListener('asr:transcribed', e => console.log(e.detail.text))
// The legacy numeric eventCount dispatch is preserved alongside for compatibility.
function _dispatchResult(text, isError = false) {
  window.transcribed_text = text;

  // Legacy numeric event (preserve existing listener compatibility)
  if (typeof window.eventCount !== 'undefined') {
    document.dispatchEvent(new Event(window.eventCount));
    window.eventCount++;
  }

  // New typed event — listeners can use this instead
  document.dispatchEvent(new CustomEvent(ASR_CONFIG.DISPATCH_EVENT_KEY, {
    detail: { text, isError },
  }));
}

// ─── Core fetch with timeout ──────────────────────────────────────────────────
async function _asrFetchWithTimeout(url, options) {
  const timerId = setTimeout(() => ASRState.abort(), ASR_CONFIG.TIMEOUT_MS);
  try {
    const res = await fetch(url, { ...options, signal: ASRState.signal });
    clearTimeout(timerId);
    return res;
  } catch (err) {
    clearTimeout(timerId);
    throw err;
  }
}

// ─── Retry wrapper ────────────────────────────────────────────────────────────
async function _asrFetchWithRetry(url, options) {
  let lastErr;
  for (let attempt = 1; attempt <= ASR_CONFIG.MAX_RETRIES; attempt++) {
    try {
      return await _asrFetchWithTimeout(url, options);
    } catch (err) {
      if (err.name === 'AbortError') throw err;
      lastErr = err;
      if (attempt < ASR_CONFIG.MAX_RETRIES) {
        _asrShowRetryMessage(attempt, ASR_CONFIG.MAX_RETRIES);
        await new Promise(r => setTimeout(r, ASR_CONFIG.RETRY_BASE_MS * Math.pow(2, attempt - 1)));
      }
    }
  }
  throw lastErr;
}

// ─────────────────────────────────────────────────────────────────────────────
// transcribeAudioVosk  — local / on-device ASR endpoint
// ─────────────────────────────────────────────────────────────────────────────
/**
 * @param {Blob}   sound           - Raw audio blob from MediaRecorder
 * @param {string} audio_file_name - Filename for logging / server use
 */
async function transcribeAudioVosk(sound, audio_file_name) {
  // ── Validate ──
  if (!(sound instanceof Blob) || sound.size === 0) {
    console.warn('ASR Vosk: invalid or empty audio blob — skipped');
    return;
  }
  if (sound.size > ASR_CONFIG.MAX_FILE_SIZE_BYTES) {
    console.warn(`ASR Vosk: file too large (${sound.size} bytes) — skipped`);
    _asrShowFinalError('Recording too long. Please keep responses under ~30 seconds.');
    return;
  }
  if (ASRState.isDuplicate(sound)) {
    console.warn('ASR Vosk: duplicate blob — skipped');
    return;
  }

  // ── Offline guard ──
  if (!ASRNetworkMonitor.isOnline) {
    ASRState.enqueue({ type: 'vosk', sound, audio_file_name });
    _asrShowOfflineBanner(true);
    return;
  }

  // ── Cancel any in-flight request ──
  if (ASRState.isLoading) {
    console.warn('ASR Vosk: cancelling previous request');
    ASRState.abort();
    await new Promise(r => setTimeout(r, 0));
  }

  ASRState.startRequest();
  _asrLockMic(true);
  _asrShowOverlay();

  const slowTimer = setTimeout(
    () => _asrSetMessage('Slow network — still processing audio…'),
    ASR_CONFIG.SLOW_NET_WARN_MS,
  );

  const formData = new FormData();
  formData.append('audio', sound, audio_file_name);

  try {
    const res = await _asrFetchWithRetry(recogonize_local, {
      method: 'POST',
      body:   formData,
    });

    if (!res.ok) {
      throw new ASRError(`HTTP ${res.status}`, res.status);
    }

    const data = await res.json();
    const text = data?.response ?? '';

    if (!text) {
      console.warn('ASR Vosk: empty transcription returned');
    }

    console.log('ASR Vosk response:', text);
    _dispatchResult(text);

  } catch (err) {
    if (err.name === 'AbortError') {
      console.info('ASR Vosk: request aborted');
      return;
    }
    console.error('ASR Vosk error:', err);
    _dispatchResult('error-asr-vosk', true);
    _asrShowFinalError('Could not transcribe audio. Please try again.');
  } finally {
    clearTimeout(slowTimer);
    _asrHideOverlay();
    _asrLockMic(false);
    ASRState.endRequest();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// transcribeAudioProxy  — remote / Bhashini ASR endpoint
// ─────────────────────────────────────────────────────────────────────────────
/**
 * @param {Blob}   blob             - Raw audio blob
 * @param {string} serviceId_ASR    - Bhashini service identifier
 * @param {string} audio_filename   - Filename for the server
 */
async function transcribeAudioProxy(blob, serviceId_ASR, audio_filename) {
  // ── Validate ──
  if (!(blob instanceof Blob) || blob.size === 0) {
    console.warn('ASR Proxy: invalid or empty audio blob — skipped');
    return;
  }
  if (ASRState.isDuplicate(blob)) {
    console.warn('ASR Proxy: duplicate blob — skipped');
    return;
  }

  // ── Offline guard ──
  if (!ASRNetworkMonitor.isOnline) {
    ASRState.enqueue({ type: 'proxy', blob, serviceId_ASR, audio_filename });
    _asrShowOfflineBanner(true);
    return;
  }

  // ── Cancel any in-flight request ──
  if (ASRState.isLoading) {
    console.warn('ASR Proxy: cancelling previous request');
    ASRState.abort();
    await new Promise(r => setTimeout(r, 0));
  }

  ASRState.startRequest();
  _asrLockMic(true);
  _asrShowOverlay();
  
  window.response_wait_audio?.load();
  window.response_wait_audio?.play();

  const slowTimer = setTimeout(
    () => _asrSetMessage('Slow network — still processing audio…'),
    ASR_CONFIG.SLOW_NET_WARN_MS,
  );

  const formData = new FormData();
  formData.append('language',   window.asrLanguage ?? '');
  formData.append('audio',      blob, audio_filename);
  formData.append('service_id', serviceId_ASR);
  formData.append('file_name',  audio_filename);

  try {
    const res = await _asrFetchWithRetry(recogonize_remote, {
      method: 'POST',
      body:   formData,
    });

    if (res.status === 500) {
      // Known server-side failure — dispatch sentinel so caller can handle it
      console.warn('ASR Proxy: server returned 500');
      _dispatchResult('error-500', true);
      return;
    }

    if (!res.ok) {
      throw new ASRError(`HTTP ${res.status}`, res.status);
    }

    const data = await res.json();
    const text = data?.text ?? '';

    if (!text) {
      console.warn('ASR Proxy: empty transcription returned');
    }

    console.log('ASR Proxy response:', text);
    _dispatchResult(text);

  } catch (err) {
    if (err.name === 'AbortError') {
      console.info('ASR Proxy: request aborted');
      // Still dispatch so the UI doesn't hang waiting for the event
      _dispatchResult('error-aborted', true);
      return;
    }
    console.error('ASR Proxy error:', err);
    _dispatchResult('error-network', true);
    _asrShowFinalError('Speech recognition failed. Check your connection and try again.');
  } finally {
    clearTimeout(slowTimer);
    _asrHideOverlay();
    _asrLockMic(false);
    window.response_wait_audio?.pause();
    ASRState.endRequest();
  }
}

// ─── Flush offline queue when network returns ─────────────────────────────────
async function _flushASRQueue() {
  _asrShowOfflineBanner(false);
  console.info(`ASR: back online — flushing ${ASRState.queue.length} queued item(s)`);

  while (ASRState.queue.length > 0) {
    const item = ASRState.dequeue();
    if (!item) break;

    if (item.type === 'vosk') {
      await transcribeAudioVosk(item.sound, item.audio_file_name);
    } else {
      await transcribeAudioProxy(item.blob, item.serviceId_ASR, item.audio_filename);
    }

    await new Promise(r => setTimeout(r, 300)); // brief pause between items
  }
}

// ─── Custom error class ───────────────────────────────────────────────────────
class ASRError extends Error {
  constructor(message, status = null) {
    super(message);
    this.name   = 'ASRError';
    this.status = status;
  }
}

// ─── Export (remove if not using modules) ────────────────────────────────────
// export { transcribeAudioVosk, transcribeAudioProxy, ASRState, ASR_CONFIG };