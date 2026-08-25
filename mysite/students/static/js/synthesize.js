var audio = new Audio();
var audio_wait = new Audio();

var isPlaying = false;
// to get service id if language changes
var previous_lang;
var generated_audio_file_name = "";
var audio_file_name = "";

var speakerButton = document.getElementById("speakerButton");
const playbackSpeedControl = document.getElementById('playback_speed');
const display_playback_speed = document.getElementById('display_playback_speed');
var playback_speed = parseFloat(localStorage.getItem(userID + "_playback_speed")) || 1.0;
playbackSpeedControl.value = playback_speed;
display_playback_speed.innerHTML = playback_speed + "x";
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
        console.log("TTS: text: ", text)

        synthesisAudioProxy(text, service_id_tts, lang);
    }
}

// function synthesisAudioProxy(text, serviceIdTTS, lang) {

//     text_filename = userID.trim() + "_tts_" + getDateTime() + ".txt"

//     const TTSFormData = new FormData();
//     TTSFormData.append("language", lang);
//     TTSFormData.append("text", text);
//     TTSFormData.append("service_id", serviceIdTTS);
//     TTSFormData.append("file_name", text_filename);
//     // TTSFormData.append("user_id", userID);


//     var oReq = new XMLHttpRequest();
//     // oReq.open("POST", TTS_API_BHASHINI_PROXY, true);
//     oReq.open("POST", synthesize_remote, true);
//     oReq.onload = function (oEvent) {
//         if (oReq.status == 200) {
//             // console.log("TTS Response: ", oReq.response);
//             tts_response = oReq.response;
//             const obj = JSON.parse(tts_response);

//             audio_base_64 = obj.audio
//             state = document.getElementById("stop_resume").innerHTML

//             if (state == "Resume") {
//                 audio_wait.src = "data:audio/wav;base64," + audio_base_64;
//                 audio_wait.load();
//                 audio_wait.play();
                
//                 audio_wait.playbackRate = playback_speed
//             } else {
//                 audio.pause();
//                 audio.src = "data:audio/wav;base64," + audio_base_64;
//                 audio.load();
//                 audio.play();
//                 audio.playbackRate = playback_speed
//                 isPlaying = true;
//                 speakerButton.classList.add("speakering");
//                 speakerButton.style.backgroundColor = 'yellow'
//             }
//         }
//         if (oReq.status === 500) {
//             transcribed_text = "not able to synthesis"
//             // console.log("Trying our TTS")
//             // synthesizeSpeechIndia(text);

//         }
//         response_wait_audio.pause();
//         JsLoadingOverlay.hide();
//     };
//     console.log("Sending text... ");
//     JsLoadingOverlay.show({
//         'overlayBackgroundColor': '#ffffff',
//         'spinnerIcon': 'ball-beat'
//     });
//     response_wait_audio.load();
//     response_wait_audio.play();

//     oReq.send(TTSFormData);
// }


// ─────────────────────────────────────────────────────────────────────────────
// Robust TTS Proxy — exam-grade reliability
// Handles: slow networks, disconnects, retries, duplicate calls, state leaks
// ─────────────────────────────────────────────────────────────────────────────

const TTS_CONFIG = {
  TIMEOUT_MS:        20_000,   // abort a single fetch after 20s
  MAX_RETRIES:       3,        // attempts before giving up
  RETRY_BASE_MS:     800,      // first retry delay; doubles each attempt
  SLOW_NET_WARN_MS:  8_000,    // show "slow network" notice after this
  MAX_QUEUE_SIZE:    10,       // don't let the offline queue grow unbounded
  DEDUPE_WINDOW_MS:  300,      // ignore identical calls within this window
};

// ─── Singleton state ──────────────────────────────────────────────────────────
const TTSState = (() => {
  let _isLoading     = false;
  let _currentReqId  = null;
  let _lastText      = null;
  let _lastCallAt    = 0;
  let _abortCtrl     = null;
  const _queue       = [];     // offline queue: [{text, serviceId, lang, id}]
  const _listeners   = new Set();

  return {
    get isLoading()    { return _isLoading; },
    get currentReqId() { return _currentReqId; },
    get queue()        { return _queue; },

    startRequest(id) {
      _isLoading    = true;
      _currentReqId = id;
      _abortCtrl    = new AbortController();
      this._emit('start', id);
    },
    endRequest(err) {
      _isLoading    = false;
      _currentReqId = null;
      _abortCtrl    = null;
      this._emit(err ? 'error' : 'done', err);
    },
    abort() {
      _abortCtrl?.abort();
    },
    get signal() {
      return _abortCtrl?.signal;
    },

    isDuplicate(text) {
      const now   = Date.now();
      const isDup = text === _lastText && (now - _lastCallAt) < TTS_CONFIG.DEDUPE_WINDOW_MS;
      _lastText   = text;
      _lastCallAt = now;
      return isDup;
    },

    enqueue(item) {
      if (_queue.length >= TTS_CONFIG.MAX_QUEUE_SIZE) _queue.shift(); // drop oldest
      _queue.push(item);
    },
    dequeue() { return _queue.shift(); },

    on(cb) { _listeners.add(cb); },
    off(cb) { _listeners.delete(cb); },
    _emit(event, data) { _listeners.forEach(cb => { try { cb(event, data); } catch {} }); },
  };
})();

// ─── Network monitor ──────────────────────────────────────────────────────────
const NetworkMonitor = (() => {
  let _online = navigator.onLine;

  window.addEventListener('online',  () => { _online = true;  _flushQueue(); });
  window.addEventListener('offline', () => { _online = false; _showOfflineBanner(true); });

  return {
    get isOnline() { return _online; },
  };
})();

// ─── UI helpers (adapt to your overlay/banner system) ────────────────────────
function _showOverlay(msg = '') {
  if (typeof JsLoadingOverlay !== 'undefined') {
    JsLoadingOverlay.show({ overlayBackgroundColor: '#ffffff', spinnerIcon: 'ball-beat' });
  }
  if (msg) _setOverlayMessage(msg);
}

function _hideOverlay() {
  if (typeof JsLoadingOverlay !== 'undefined') JsLoadingOverlay.hide();
  _setOverlayMessage('');
}

function _setOverlayMessage(msg) {
  // Inject a message node into your overlay if your library supports it,
  // otherwise use a dedicated DOM element:
  let el = document.getElementById('tts-overlay-msg');
  if (!el) {
    el = document.createElement('div');
    el.id = 'tts-overlay-msg';
    el.style.cssText =
      'position:fixed;top:60px;left:50%;transform:translateX(-50%);' +
      'background:#333;color:#fff;padding:8px 16px;border-radius:6px;' +
      'font-size:14px;z-index:9999;display:none;';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = msg ? 'block' : 'none';
}

function _showOfflineBanner(visible) {
  _setOverlayMessage(visible ? '⚠ No internet connection — will retry when reconnected.' : '');
}

function _showRetryError(attempt, maxRetries) {
  _setOverlayMessage(`Network issue — retrying (${attempt}/${maxRetries})…`);
}

function _showFinalError(msg) {
  _hideOverlay();
  _setOverlayMessage('');
  // Replace with your app's error toast / modal as needed:
  const el = document.getElementById('tts-error-banner') || (() => {
    const d = document.createElement('div');
    d.id = 'tts-error-banner';
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

// ─── Core fetch with timeout + signal ────────────────────────────────────────
async function _fetchWithTimeout(url, options, timeoutMs) {
  const timeoutId = setTimeout(() => TTSState.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: TTSState.signal });
    clearTimeout(timeoutId);
    return res;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}

// ─── Retry wrapper with exponential back-off ──────────────────────────────────
async function _fetchWithRetry(url, options) {
  let lastErr;
  for (let attempt = 1; attempt <= TTS_CONFIG.MAX_RETRIES; attempt++) {
    try {
      const res = await _fetchWithTimeout(url, options, TTS_CONFIG.TIMEOUT_MS);
      return res;
    } catch (err) {
      if (err.name === 'AbortError') throw err;         // user-cancelled — bail
      lastErr = err;
      if (attempt < TTS_CONFIG.MAX_RETRIES) {
        _showRetryError(attempt, TTS_CONFIG.MAX_RETRIES);
        const delay = TTS_CONFIG.RETRY_BASE_MS * Math.pow(2, attempt - 1);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }
  throw lastErr;
}

// ─── Audio playback helper ────────────────────────────────────────────────────
async function _playAudio(base64, isStopped) {
  const src = 'data:audio/wav;base64,' + base64;
  const target = isStopped ? window.audio_wait : window.audio;

  if (!target) {
    console.error('TTS: audio element not found');
    return;
  }

  target.src = src;
  target.load();
  
 try {
    await target.play();
    target.playbackRate = window.playback_speed ?? 1;
   
    if (!isStopped) {
      window.isPlaying = true;
      window.speakerButton?.classList.add('speakering');
      if (window.speakerButton) window.speakerButton.style.backgroundColor = 'yellow';
    }
  } catch (err) {
      console.warn('TTS audio play failed:', err);
      // additional statements
      
  }
}

// ─── Main public function ─────────────────────────────────────────────────────
/**
 * synthesisAudioProxy
 *
 * @param {string} text          - Text to synthesise
 * @param {string} serviceIdTTS  - TTS service identifier
 * @param {string} lang          - BCP-47 language code
 * @returns {Promise<void>}
 */
async function synthesisAudioProxy(text, serviceIdTTS, lang) {
  // ── Guard: empty input ──
  if (!text?.trim()) {
    console.warn('TTS: empty text — skipped');
    return;
  }

  // ── Guard: debounce duplicate calls ──
  if (TTSState.isDuplicate(text)) {
    console.warn('TTS: duplicate call within debounce window — skipped');
    return;
  }

  // ── Guard: offline → queue and bail ──
  if (!NetworkMonitor.isOnline) {
    TTSState.enqueue({ text, serviceIdTTS, lang, id: _makeId() });
    _showOfflineBanner(true);
    console.warn('TTS: offline — queued for later');
    return;
  }

  // ── Guard: already loading → cancel previous ──
  if (TTSState.isLoading) {
    console.warn('TTS: cancelling previous in-flight request');
    TTSState.abort();
    // small yield so the previous fetch sees its AbortError before we proceed
    await new Promise(r => setTimeout(r, 0));
  }

  const reqId = _makeId();
  TTSState.startRequest(reqId);

  // ── Build FormData ──
  // const filename = (window.userID ?? 'user').trim() + '_tts_' + _getDateTime() + '.txt';

  const formData = new FormData();
  formData.append('language',   lang);
  formData.append('text',       text);
  formData.append('service_id', serviceIdTTS);
  formData.append('file_name',  audio_file_name );

  // ── UI: show overlay + waiting audio ──
  _showOverlay();
  const slowTimer = setTimeout(
    () => _setOverlayMessage('Slow network — still working…'),
    TTS_CONFIG.SLOW_NET_WARN_MS,
  );

  window.response_wait_audio?.load();
  window.response_wait_audio?.play();

  try {
    const res = await _fetchWithRetry(synthesize_remote, {
      method: 'POST',
      body:   formData,
    });

    // ── HTTP-level errors ──
    if (!res.ok) {
      const errText = await res.text().catch(() => '');
      throw new TTSError(`HTTP ${res.status}`, res.status, errText);
    }

    const data = await res.json();

    if (!data?.audio) {
      throw new TTSError('Response missing audio field');
    }

    // ── Play audio ──
    const isStopped = document.getElementById('stop_resume')?.dataset.state === 'resume';
    generated_audio_file_name = data.filename; // fallback to generated name
    _playAudio(data.audio, isStopped);

    TTSState.endRequest(null);
  } catch (err) {
    TTSState.endRequest(err);

    if (err.name === 'AbortError') {
      console.info('TTS: request aborted');
      return;  // not an error — just cancelled
    }

    console.error('TTS error:', err);

    const userMsg = err instanceof TTSError && err.status === 500
      ? 'Speech synthesis failed (server error). Please try again.'
      : 'Could not connect to speech service. Check your connection.';

    _showFinalError(userMsg);
  } finally {
    clearTimeout(slowTimer);
    _hideOverlay();
    window.response_wait_audio?.pause();
    audio_file_name = ""; // reset for next call
  }
}

// ─── Flush offline queue when network recovers ────────────────────────────────
async function _flushQueue() {
  _showOfflineBanner(false);
  console.info(`TTS: back online — flushing ${TTSState.queue.length} queued request(s)`);

  while (TTSState.queue.length > 0) {
    const item = TTSState.dequeue();
    if (item) {
      await synthesisAudioProxy(item.text, item.serviceIdTTS, item.lang);
      // Small gap between queued items to avoid hammering the server
      await new Promise(r => setTimeout(r, 300));
    }
  }
}

// ─── Custom error class ───────────────────────────────────────────────────────
class TTSError extends Error {
  constructor(message, status = null, body = '') {
    super(message);
    this.name   = 'TTSError';
    this.status = status;
    this.body   = body;
  }
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function _makeId() {
  return Math.random().toString(36).slice(2, 9);
}

function _getDateTime() {
  // Replace with your existing getDateTime() if you have one
  return new Date().toISOString().replace(/[:.]/g, '-');
}

// ─── Export (remove if not using modules) ────────────────────────────────────
// export { synthesisAudioProxy, TTSState, NetworkMonitor, TTS_CONFIG };


playbackSpeedControl.addEventListener('input', e => {
    const value = parseFloat(e.target.value);

    setPlaybackSpeedRate(value)

});



function setPlaybackSpeedRate(rate) {
  const rounded = Math.round(rate / STEP) * STEP;
  
  playback_speed = Math.min(
    MAX,
    Math.max(MIN, Number(rounded.toFixed(2)))
  );
  
    localStorage.setItem(userID + "_playback_speed", playback_speed);

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
        text = playback_speed + " " + "times slower";
    } else {
        text = playback_speed + " " + "times faster";
    }

    playbackSpeedControl.setAttribute('aria-valuetext', text);
}
  