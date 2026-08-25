
from django.urls import path
from . import views


urlpatterns = [
    path("get_model/", views.speech_models_view, name="speech_models"),
    path("recogonize_local/", views.vosk_limited_vocab_asr, name="recogonize_local"),
    path("recogonize_remote/", views.asr_proxy, name="recogonize_remote"),
    path("synthesize_remote/", views.tts_proxy, name="synthesize_remote"),
    path("get_audio_file/<str:username>/<str:audio_filename>/", views.get_audio_file, name="get_audio_file"),
]
