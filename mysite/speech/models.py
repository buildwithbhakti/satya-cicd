from django.db import models

import hashlib

class SpeechModels(models.Model):
    TASK_CHOICES = [
    ('asr', 'ASR'),
    ('tts', 'TTS'),
    ]
    LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
    ('mr', 'Marathi'),
    ]
    task = models.CharField(max_length=3, choices = TASK_CHOICES)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    service_id = models.CharField(max_length=100)
    selected = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    objects = models.Manager()

    def __str__(self):
        return f'{self.task} - {self.language} - {self.selected}'
    

def tts_audio_path(instance, filename):
    return f"audios/tts/{instance.text_hash}.wav"


class TTSCached(models.Model):
    text = models.TextField()
    text_hash = models.CharField(max_length=64, unique=True, db_index=True)
    model_name = models.CharField(max_length=128, db_index=True)
    audio_file = models.FileField(upload_to=tts_audio_path, null=True, blank=True)
    hit_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.text_hash:
            key = (self.text or '') + '|' + (self.model_name or '')
            self.text_hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)
    
from students.models import Answers
class AnswerAudio(models.Model):
    answer = models.ForeignKey(Answers, related_name='audios', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)   # or use FileField / models.URLField
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.answer.user} - {self.answer.test}'

