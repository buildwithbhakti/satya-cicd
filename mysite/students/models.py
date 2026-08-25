from django.db import models
from accounts.models import CustomUser
from evaluate.utils.encrypt import EncryptedTextField
from teachers.models import Tests, Questions, QuestionOption, MatchItem

class Answers(models.Model):
    user = models.ForeignKey(CustomUser, related_name='test_given_by', on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)

    option = models.ForeignKey(QuestionOption, related_name='selected_option', on_delete=models.CASCADE, blank=True, null=True)
    
    # answer = models.TextField(blank=True)
    answer = EncryptedTextField()

    status = models.CharField(max_length=20, blank=True)    

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} - {self.test} - {self.question.question_type}'
    
    class Meta:
        verbose_name_plural = "Answers"

class Attempts(models.Model):
    user = models.ForeignKey(CustomUser, related_name='attempts_by', on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)

    submitted = models.BooleanField(default=False)
    retake = models.BooleanField(default=False)
    evaluated = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)


    start_time = models.DateTimeField(auto_now_add=True)  # automatically set when attempt starts
    end_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-start_time']  # Most recent first
        verbose_name_plural = "Attempts"

    def __str__(self):
        return f'{self.user} - {self.test} - Submitted: {self.submitted}'

class MatchedPair(models.Model):
    answer = models.ForeignKey(Answers, related_name='selected_match_pairs', on_delete=models.CASCADE)
    item_a = models.ForeignKey(MatchItem, related_name='+', on_delete=models.CASCADE)
    item_b = models.ForeignKey(MatchItem, related_name='+', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.item_a.label} => {self.item_b.label}'

class SelectedOption(models.Model):
    answer = models.ForeignKey(Answers, related_name='selected_options',  on_delete=models.CASCADE)
    option = models.ForeignKey(QuestionOption,related_name='+', on_delete=models.CASCADE)



class TestLogs(models.Model):
    MODE_CHOICES = [
    ('speech', 'Speech'),
    ('system', 'System'),
    ('keyboard', 'Keyboard'),
    ]
    TYPE_CHOICES = [
    ('info', 'Info'),
    ('error', 'Error'),
    ('command', 'Command'),
    ('answer', 'Answer'),
    ('violation', 'Violation'),
    ('other', 'Other'),
    ]
    user = models.ForeignKey(CustomUser, related_name='test_logs', on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(choices=TYPE_CHOICES, default='info')
    mode = models.CharField(choices=MODE_CHOICES, default='system')
    activity = models.CharField(max_length=200, blank=True)
    function = models.CharField(max_length=200, blank=True)
    page = models.CharField(max_length=100, blank=True)
    audio_filename = models.CharField(max_length=200, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)
    ip_address = models.GenericIPAddressField(blank=True , null=True)
    timestamp = models.DateTimeField(auto_now_add=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'test', '-version'], name='testlog_version_idx'),
            models.Index(fields=['test', '-timestamp'], name='testlog_test_time_idx'),
        ]
        verbose_name_plural = "TestLogs"

    def __str__(self):
        return f'{self.user} - {self.test} - {self.type} at {self.timestamp}'