from django.shortcuts import render
from django.http import FileResponse, JsonResponse
from .models import SpeechModels
from .models import TTSCached
from .utils import text_hash, normalize_text

from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError, models as djmodels

from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.views.decorators.http import require_GET
from django.conf import settings
from sarvamai import SarvamAI

from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
import wave, requests, requests, base64, json, logging, os, io
from piper import PiperVoice


BHASHINI_API = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

API_KEY = "2Vcwl7OGNkdstV-4B8YTuB4s-PpacoX9VXlzjtn1Gq5GOjM8j-oEmbRzDf4GkcXd"
headers = {'Content-type': 'application/json', 'Authorization': API_KEY}

# LOG_FILE = os.path.join(settings.LOG_FILES_DIR, "speech.log")
# ASR_MODEL_PATH = os.path.join(settings.MODEL_FILES_DIR, "vosk-model-small-en-in-0.4")
ASR_MODEL_PATH = os.path.join(settings.MODEL_FILES_DIR, "vosk-model-small-en-us-0.15")

MAX_DURATION_SEC = 28  # safely under Sarvam's 30s limit

client = SarvamAI(
    api_subscription_key="sk_mg0exhxv_JQQ3XlhSy2nF7RRe2SnxkZe4",
)
# logging.basicConfig(format='%(asctime)s - %(message)s', filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger(__name__) 

@csrf_exempt
@require_http_methods(["POST"])
def speech_models_view(request):
 
    try:
        data = json.loads(request.body.decode('utf-8') or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    task = data.get("task")
    language = data.get("language")
    selected = data.get("selected", True)
    # print(task, language)

    try:
        if selected is True:
            obj = SpeechModels.objects.get(task=task, language=language, selected=True)
            return JsonResponse({"service_id": obj.service_id})
        else:
            objs = SpeechModels.objects.filter(task=task, language=language)
            service_ids = list(objs.values_list("service_id", flat=True))
            return JsonResponse({"service_ids": service_ids})
    except SpeechModels.DoesNotExist:
        return JsonResponse({"error": "No selected service found"}, status=204)



# ASR for command mode


model = Model(ASR_MODEL_PATH)
words_list = '["five", "four", "review", "return", "instructions", "system", "next", "option", "previous", "question", "submit", "true", "false", "three", "start", "two", "repeat", "write", "answer", "one", "yes", "no", "read", "delete", "point", "exam", "status", "time", "remaining", "help", "six", "matching", "highlight", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "wait", "count", "words", "replace", "mark", "clear", "all", "note", "add", "[unk]"]'
WORD_TO_DIGIT = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten" : "10", "elevan" : "11", "twelve" : "12", 
    "thirteen" : "13" , "fourteen" : "14", "fifteen": "15", "sixteen": "16", "seventeen" : "17",
    "eighteen" : "18", "nineteen" : "19", "twenty" : "20"
}
def convert_last_word_to_digit(text: str) -> str:
    text = text.rstrip()
    head, sep, tail = text.rpartition(" ")
    d = WORD_TO_DIGIT.get(tail.lower())
    return f"{head}{sep}{d}" if d else text

@csrf_exempt 
@require_http_methods(["POST"])
def vosk_limited_vocab_asr(request):

    audio = request.FILES.get('audio')
    if not audio:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    dir = os.path.join(default_storage.location, 'audios', 'asr', request.user.username)
    os.makedirs(dir, exist_ok=True)
    audio_file_path = os.path.join(dir, audio.name)

    audio.seek(0)
    with open(audio_file_path, 'wb') as f:
        for chunk in audio.chunks():
            f.write(chunk) 
    
    audio.seek(0)
    wf = wave.open(audio)

    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
        return JsonResponse({'error': 'Issue with audio format'}, status=400)

    rec = KaldiRecognizer(model, wf.getframerate(),words_list)
    data = wf.readframes(wf.getnframes())

    if len(data) == 0:
        raise ValueError("Empty audio")
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
    else:
        result = json.loads(rec.FinalResult())

    text = convert_last_word_to_digit(result["text"])
    print("asr out: ", text)

    return JsonResponse({"success": True, "response": text})

# ASR Bhashini
def sendDataToBhasiniServerASR(language, service_id, base64data):
    payload = {
            "pipelineTasks": [{
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": language
                        },
                        "serviceId": service_id,
                        "preProcessors": ["vad"]
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

    response_asr = requests.post(BHASHINI_API, data=json.dumps(payload), headers=headers)
 
    response_json_asr = json.loads(response_asr.text)
    recognized_text_asr = response_json_asr["pipelineResponse"][0]["output"][0]["source"]

    return recognized_text_asr

def split_audio_segment(audio_segment: AudioSegment, max_sec: float = MAX_DURATION_SEC) -> list[AudioSegment]:
    max_ms = int(max_sec * 1000)
    return [audio_segment[start:start + max_ms] for start in range(0, len(audio_segment), max_ms)]

def segment_to_wav_bytes(segment: AudioSegment) -> bytes:
    buf = io.BytesIO()
    segment.export(buf, format="wav")
    return buf.getvalue()


@csrf_exempt
@require_http_methods(["POST"])
def asr_proxy(request):
    language = request.POST.get('language')
    service_id = request.POST.get('service_id')
    uploaded_file = request.FILES.get('audio')
    filename_wav = request.POST.get('file_name')
    user_id = request.user.username

    if not uploaded_file or not filename_wav:
        return JsonResponse({'error': 'audio and file_name required'}, status=400)

    logger.info(f"ASR :: > : {user_id} {language} {filename_wav}")

    relative_dir = os.path.join('audios', 'asr', user_id)
    audio_file_path = os.path.join(relative_dir, filename_wav)
    abs_dir = os.path.join(default_storage.location, relative_dir)
    os.makedirs(abs_dir, exist_ok=True)

    # Save uploaded file once; reuse the absolute path everywhere
    saved_path = default_storage.save(audio_file_path, uploaded_file)
    abs_audio_path = os.path.join(default_storage.location, saved_path)

    # Load audio once — used for duration and possibly for Bhasini base64
    audio_segment = AudioSegment.from_file(abs_audio_path)
    total_duration = round(audio_segment.duration_seconds, 2)
    logger.info(f"ASR :: > : {user_id} {language} {filename_wav} {total_duration}")

    # --- Transcription ---
    try:
        if service_id == "sarvam":
            lang = f"{language}-IN"

            if total_duration <= MAX_DURATION_SEC:
                # Fast path — under limit, use saved file directly
                with open(abs_audio_path, "rb") as f:
                    response = client.speech_to_text.transcribe(
                        file=f,
                        model="saaras:v3",
                        mode="transcribe",
                        language_code=lang,
                    )
                transcript = response.transcript
            else:
                # Long audio — split and transcribe each chunk
                chunks = split_audio_segment(audio_segment)
                logger.info(f"ASR :: splitting into {len(chunks)} chunks: {user_id} {filename_wav} {total_duration}s")
                parts = []
                for i, chunk in enumerate(chunks):
                    wav_bytes = segment_to_wav_bytes(chunk)
                    response = client.speech_to_text.transcribe(
                        file=("chunk.wav", io.BytesIO(wav_bytes), "audio/wav"),
                        model="saaras:v3",
                        mode="transcribe",
                        language_code=lang,
                    )
                    parts.append(response.transcript)
                    logger.info(f"ASR :: chunk {i+1}/{len(chunks)} done: {user_id}")
                transcript = " ".join(parts)
        else:
            # Export to wav in-memory — avoids a second disk read
            audio_base64 = base64.b64encode(
                audio_segment.export(format="wav").read()
            ).decode('utf-8')
            transcript = sendDataToBhasiniServerASR(language, service_id, audio_base64)
            
    except Exception as e:
        logger.error(f"ASR transcription failed: {user_id} {language} {filename_wav} — {e}")
        return JsonResponse({'error': 'transcription failed'}, status=500)

    # --- Persist transcript ---
    txt_filename = os.path.splitext(filename_wav)[0] + ".txt"
    abs_txt_path = os.path.join(abs_dir, txt_filename)
    try:
        with open(abs_txt_path, "w", encoding='utf-8') as f:
            f.write(transcript)
    except OSError as e:
        logger.warning(f"ASR failed to write transcript file: {e}")
        # Non-fatal — still return the transcript to the caller

    logger.info(f"ASR :: < : {user_id} {language} {txt_filename} {len(transcript)}")
    return JsonResponse({'success': True, 'text': transcript}, status=200)



# TTS Bhashini
def sendDataToBhasiniServerTTS(language, service_id, text):
    payload = {
          "pipelineTasks": [{
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": language
                    },
                    "serviceId": service_id,
                    "gender": "female"
                }
            }
        ],
        "inputData": {
            "input": [{
                    "source": text
                }
            ],
            "audio": [{
                    "audioContent": "null"
                }
            ]
        }
        }

    response_tts = requests.post(BHASHINI_API, data=json.dumps(payload), headers=headers)

    # Parse ASR API response and extract recognized text
    response_json_asr = json.loads(response_tts.text)
    audio_base_64 = response_json_asr["pipelineResponse"][0]["audio"][0]["audioContent"]

    return audio_base_64


@csrf_exempt
@require_http_methods(["POST"])
def tts_proxy(request):
    text = request.POST.get('text')
    language = request.POST.get('language')
    model_name = request.POST.get('service_id')
    file_name = request.POST.get('file_name')
    user_id = request.user.username

    if not text:
        return JsonResponse({'error': 'text required'}, status=400)
   
    if (file_name == ""):
        key = text_hash(text, model_name)
        filename = f"{key}.wav"
        logger.info(f"TTS :: > : {user_id} {language} {key} {len(text)}")
    else:
        key = file_name.rsplit('.', 1)[0]  # remove extension for hashing
        filename = file_name
        logger.info(f"TTS :: > : {user_id} {language} {key} {len(text)} : filename provided")

    # --- Cache lookup (read-only, no transaction needed) ---
    record = TTSCached.objects.filter(text_hash=key).first()
    if record:
        # Single UPDATE, no refresh_from_db needed for serving
        TTSCached.objects.filter(pk=record.pk).update(hit_count=djmodels.F('hit_count') + 1)
        audio_b64 = _read_audio_b64(record)
        logger.info(f"TTS :: < : {user_id} {language} {key} {len(text)} : cached")
        return JsonResponse({'audio': audio_b64, 'filename': filename})

    # --- Synthesize audio (expensive, do BEFORE writing to DB) ---
    try:
        audio_b64 = _synthesize(model_name, language, text)
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return JsonResponse({'error': 'synthesis failed'}, status=500)

    wav_bytes = base64.b64decode(audio_b64)
    

    # --- Single atomic write (SQLite-friendly: short, no I/O inside) ---
    try:
        with transaction.atomic():
            record, created = TTSCached.objects.get_or_create(
                text_hash=key,
                defaults={
                    'text': normalize_text(text),
                    'model_name': model_name,
                    'hit_count': 1,
                }
            )
            if not created:
                # Race condition: another request already synthesized it
                TTSCached.objects.filter(pk=record.pk).update(hit_count=djmodels.F('hit_count') + 1)
                audio_b64 = _read_audio_b64(record)
                return JsonResponse({'audio': audio_b64, 'filename': filename})

            # Save file outside transaction if possible, but keep it simple here
            record.audio_file.save(filename, io.BytesIO(wav_bytes), save=False)
            record.save(update_fields=['audio_file', 'hit_count'])

    except Exception as e:
        logger.error(f"TTS DB write failed: {e}")
        # Best-effort cleanup
        TTSCached.objects.filter(text_hash=key).delete()
        return JsonResponse({'error': 'synthesis failed'}, status=500)

    # --- Duration logger (non-critical, don't fail the request) ---
    try:
        filepath = os.path.join(default_storage.location, 'audios', 'tts', filename)
        duration = round(AudioSegment.from_file(filepath).duration_seconds, 2)
        logger.info(f"TTS :: < : {user_id} {language} {key} {duration}")
    except Exception as e:
        logger.warning(f"TTS duration calc failed: {e}")

    return JsonResponse({'audio': audio_b64, 'filename': filename})


def _read_audio_b64(record) -> str:
    with record.audio_file.open('rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def _synthesize(model_name: str, language: str, text: str) -> str:
    if model_name == "sarvam":
        lang = f"{language}-IN"
        audio = client.text_to_speech.convert(
            target_language_code=lang,
            text=text,
            model="bulbul:v3",
            speaker="shubh",
            enable_preprocessing=True,
            pace=0.9,
            temperature=0.4,
        )
        return "".join(audio.audios)
    elif model_name == "piper-tts":
            
            voice = PiperVoice.load(os.path.join(settings.MODEL_FILES_DIR, f"{language}-piper.onnx"))

            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)          # set according to your voice (mono/stereo)
                wf.setsampwidth(2)         # bytes per sample (e.g. 2 for 16-bit)
                wf.setframerate(16000)     # sampling rate expected by the model
                voice.synthesize_wav(text, wf)
            wav_bytes = buf.getvalue()
            return base64.b64encode(wav_bytes).decode("ascii")
    else:
        return sendDataToBhasiniServerTTS(language, model_name, text)


@require_GET
def get_audio_file(request, username, audio_filename):
    # extension check
    _, file_extension = os.path.splitext(audio_filename)
    if file_extension.lower() != ".wav":
        return JsonResponse({"success": False, "error": "file is not wav"}, status=200)

    # build paths
    path_to_file = os.path.join(os.path.join(default_storage.location,'audios', 'asr', username, audio_filename))

    if os.path.exists(path_to_file) and os.path.isfile(path_to_file):
        # streams file efficiently; as_attachment=False serves inline
        return FileResponse(open(path_to_file, "rb"), content_type="audio/wav")
    else:
        return JsonResponse({"success": False, "error": "file not found!"}, status=200)