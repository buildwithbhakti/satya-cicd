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


BHASHINI_API = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

API_KEY = "2Vcwl7OGNkdstV-4B8YTuB4s-PpacoX9VXlzjtn1Gq5GOjM8j-oEmbRzDf4GkcXd"
headers = {'Content-type': 'application/json', 'Authorization': API_KEY}

LOG_FILE = os.path.join(settings.LOG_FILES_DIR, "speech.log")
MODEL_PATH = os.path.join(settings.MODEL_FILES_DIR, "vosk-model-small-en-in-0.4")

client = SarvamAI(
    api_subscription_key="sk_mg0exhxv_JQQ3XlhSy2nF7RRe2SnxkZe4",
)

logging.basicConfig(format='%(asctime)s - %(message)s', filename=LOG_FILE, level=logging.INFO)

@csrf_exempt
@require_http_methods(["POST"])
def speech_models_view(request):
 
    try:
        data = json.loads(request.body.decode('utf-8') or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    task = data.get("task")
    language = data.get("language")
    # print(task, language)

    try:
        obj = SpeechModels.objects.get(task=task, language=language, selected=True)
    except SpeechModels.DoesNotExist:
        return JsonResponse({"error": "No selected service found"}, status=204)

    return JsonResponse({"service_id": obj.service_id})



# ASR for command mode


model = Model(MODEL_PATH)
words_list = '["five", "four", "instructions", "next", "option", "previous", "question", "submit", "true", "false", "three", "start", "two", "repeat", "write", "answer", "one", "yes", "no", "read", "delete", "point", "exam", "status", "time", "remaining", "help", "six", "matching", "highlight", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "[unk]"]'
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

@csrf_exempt 
@require_http_methods(["POST"])
def asr_proxy(request):
    language = request.POST.get('language')
    service_id = request.POST.get('service_id')
    uploaded_file = request.FILES.get('audio')
    filename_wav = request.POST.get('file_name')

    print("REQUEST :: Language : ",language, " filename : ", filename_wav)
    user_id = request.user.username

    relative_dir = os.path.join('audios', 'asr', user_id)
    audio_file_path = os.path.join(relative_dir, filename_wav)

    saved_path = default_storage.save(audio_file_path, uploaded_file)

    audio_file = AudioSegment.from_file(os.path.join(default_storage.location, saved_path))
    total_duration = round(audio_file.duration_seconds, 2)
   
    final_recognized_text_asr = ""

    logging.info(f"ASR :: > : {user_id} {language} {filename_wav} {total_duration}")
    

    if(service_id == "sarvam"):
        lang = language + "-IN"
        response = client.speech_to_text.transcribe(
            file=open(os.path.join(default_storage.location, saved_path), "rb"),
            model="saaras:v3",
            mode="transcribe",
            language_code=lang
            )
        final_recognized_text_asr = response.transcript
    else:
        # use following two lines if vad paramter is used in request
        audio_base64 = base64.b64encode(audio_file.export(format="wav").read()).decode('utf-8')
        final_recognized_text_asr = sendDataToBhasiniServerASR(language, service_id, audio_base64)

    txt_file_name = os.path.splitext(filename_wav)[0] + ".txt"
    txt_file_path = os.path.join(relative_dir, txt_file_name)
    with open(os.path.join(default_storage.location, txt_file_path), "w", encoding='utf-8') as file:
        file.write(final_recognized_text_asr)
    
    logging.info(f"ASR :: < : {user_id} {language} {txt_file_name} {len(final_recognized_text_asr)}")

    resp = {"success": True, "text": final_recognized_text_asr}
    print("RESPONSE :: ", "reveived", resp)

    return JsonResponse(resp, status = 200)



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
    user_id = request.user.username

    if not text:
        return JsonResponse({'error': 'text required'}, status=400)

    key = text_hash(text, model_name)
    
    logging.info(f"TTS :: > : {user_id} {language} {key} {len(text)}")


    try:
        record = TTSCached.objects.get(text_hash=key)
        TTSCached.objects.filter(pk=record.pk).update(hit_count=djmodels.F('hit_count') + 1)
        record.refresh_from_db()
        with record.audio_file.open('rb') as f:
            wav_bytes = f.read()
        audio_b64 = base64.b64encode(wav_bytes).decode('ascii')
        logging.info(f"TTS :: < : {user_id} {language} {key} {len(text)} : cached")
        return JsonResponse({'audio': audio_b64})
    except TTSCached.DoesNotExist as e:
        print("TTS : Cached hash does not exist ", e)
    try:
        with transaction.atomic():
            record = TTSCached.objects.create(
                text=normalize_text(text),
                model_name=model_name,
                text_hash=key
            )
    except IntegrityError as e:
        record = TTSCached.objects.get(text_hash=key)
        TTSCached.objects.filter(pk=record.pk).update(hit_count=djmodels.F('hit_count') + 1)
        record.refresh_from_db()
        with record.audio_file.open('rb') as f:
            wav_bytes = f.read()
        audio_b64 = base64.b64encode(wav_bytes).decode('ascii')
        print("TTSIntegrityError", + e)
        return JsonResponse({'audio': audio_b64})
    try:
        if(model_name == "sarvam"):
            lang = language + "-IN"
            audio = client.text_to_speech.convert(
                        target_language_code=lang,
                        text=text,
                        model="bulbul:v3",
                        speaker="shubh"
                    )
            # print(audio.audios)
            audio_b64 = "".join(audio.audios)

        else:
            audio_b64 = sendDataToBhasiniServerTTS(language, model_name, text)
        
        wav_bytes = base64.b64decode(audio_b64)

        filename = f"{key}.wav"
        record.audio_file.save(filename, io.BytesIO(wav_bytes))

        record.hit_count = 1
        record.save(update_fields=['audio_file', 'hit_count'])

        total_duration = round(AudioSegment.from_file(os.path.join(default_storage.location,'audios', 'tts', filename)).duration_seconds, 2)
        
        logging.info(f"TTS :: < : {user_id} {language} {key} {total_duration}")
        
        return JsonResponse({'audio': audio_b64})
    except Exception as e:
        record.delete()
        print("TTS : ", e)
        return JsonResponse({'error': 'synthesis failed'}, status=500)



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