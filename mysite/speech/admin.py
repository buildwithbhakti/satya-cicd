from django.contrib import admin
from .models import SpeechModels, AnswerAudio, TTSCached



class SwitchSpeechModels(admin.ModelAdmin):
  list_display =  [field.name for field in SpeechModels._meta.fields]

admin.site.register(SpeechModels, SwitchSpeechModels)

class StudentsAnswerAudio(admin.ModelAdmin):
  list_display =  [field.name for field in AnswerAudio._meta.fields]

admin.site.register(AnswerAudio, StudentsAnswerAudio)

class TTSCachedContent(admin.ModelAdmin):
  list_display =  [field.name for field in TTSCached._meta.fields]

admin.site.register(TTSCached, TTSCachedContent)

