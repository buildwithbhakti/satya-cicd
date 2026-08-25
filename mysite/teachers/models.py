from django.db import models
from accounts.models import CustomUser, Institute
from django.utils.translation import gettext_lazy as _

from evaluate.utils.encrypt import EncryptedTextField
from evaluate.utils.hash import compute_signature

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
class Standard(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    standard = models.IntegerField()
    
    class Meta:
        unique_together = ('institute', 'standard')
    subjects = models.ManyToManyField(Subject, related_name='standards', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.standard}"
    
class Tests(compute_signature, models.Model):
    MEDIUM_TYPES = [
    ('en', 'English'),
    ('hi', _('Hindi')),
    ('mr', _('Marathi')),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    medium = models.CharField(max_length=10, choices=MEDIUM_TYPES, default='en')
    # subject = models.CharField(max_length=50)
    # standard = models.IntegerField()
    
    standard = models.ForeignKey(Standard, on_delete=models.PROTECT, null=True, blank=True, help_text="Select standard from the standard list.")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, null=True, blank=True, help_text="Select subject from the subject list.") 
    total_marks = models.PositiveIntegerField()
    time = models.DurationField(help_text="Enter duration as HH:MM:SS")

    name = models.CharField(max_length=100)

    instructions = models.TextField(blank=True, null=True)
    
    tts_model = models.CharField(max_length=100, blank=True, null=True, help_text="Select TTS service id for this test",)

    asr_model = models.CharField(max_length=100, blank=True, null=True, help_text="Select ASR service id for this test",)

    schedule = models.DateTimeField(blank=True, null=True, help_text="Schedule test for a future time. Test will be automatically activated at the scheduled time.")
    activated_at = models.DateTimeField(null=True, blank=True)

    isActive = models.BooleanField(default=False)
    readOnly = models.BooleanField(default=False, help_text="If true, test cannot be edited or deleted. Useful for tests that have already been taken by students.")
    forPractice = models.BooleanField(default=False, help_text="If true, test will be available in practice test section for students. No  need to activate such tests.")
    is_shuffled = models.BooleanField(default=False, help_text="if checked then question order will be different for each candidate")

    signature = models.CharField(max_length=64, editable=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.subject} - {self.standard}.{self.name}'
    
    SIGNABLE_FIELDS = ['user', 'medium', 'standard', 'subject', 'total_marks', 'time', 'name']


class Questions(models.Model):
    QUESTION_TYPES = [
        ('MCQ', _('Multiple Choice Question')),
        ('SA', _('Short Answer')),
        ('LA', _('Long Answer')),
        ('TF', _('True or False')),
        ('FIB', _('Fill In the Blanks')),
        ('MTF', _('Match The Following')),
        ('MSQ', _('Multiple Selection Question')),
    ]
    test = models.ForeignKey(Tests, related_name='questions', on_delete=models.CASCADE)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    # question = models.TextField()
    question = EncryptedTextField()

    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to='question_images/', blank=True, null=True)
    image_description = models.CharField(max_length=255, blank=True)

    min_words = models.PositiveIntegerField(blank=True, null=True)
    max_words = models.PositiveIntegerField(blank=True, null=True)

    is_shuffled = models.BooleanField(default=False, help_text="If true, options for this question will be shuffled for each student.") 

    # If this question was added from the question bank, keep a pointer to the
    # original "bank/root" question so we can avoid re-adding duplicates and
    # know whether it was later customized.
    bank_source_question = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='bank_copies',
    )
    is_customized = models.BooleanField(default=False)
    
    audio_file = models.CharField(max_length=80, blank=True, null=True, help_text="Path to the audio file for this question, if any.")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.test.subject} - {self.question_type} - {self.question[:10]}'
    
class QuestionOption(models.Model):
    question = models.ForeignKey(
        Questions,
        related_name='options',
        on_delete=models.CASCADE
    )
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.question.test.subject} {self.question.test.standard}.{self.question.test.name} - {self.question.question_type} - {self.option_text}'


class MatchItem(models.Model):
    question = models.ForeignKey(Questions, related_name='match_items', on_delete=models.CASCADE)
    column = models.CharField(max_length=1, choices=(('A','A'),('B','B')))
    label = models.CharField(max_length=255)   # displayed text
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.column}: {self.label}"

class MatchPair(models.Model):
    question = models.ForeignKey(Questions, related_name='match_pairs', on_delete=models.CASCADE)
    item_a = models.ForeignKey(MatchItem, related_name='+', on_delete=models.CASCADE)
    item_b = models.ForeignKey(MatchItem, related_name='+', on_delete=models.CASCADE)

class TestEvent(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    standard = models.CharField(max_length=50)
    message = models.CharField(max_length=20, default='activate')  # 'activate' or 'deactivate'
    created_at = models.DateTimeField(auto_now_add=True)

def question_paper_upload_to(instance, filename):
    return f"question_papers/{instance.test.standard.standard}/{instance.test.subject.name}/{filename}"

class QuestionPaperUpload(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    file = models.FileField(upload_to=question_paper_upload_to)
    extracted_text = models.TextField(blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} ({self.uploaded_at:%Y-%m-%d})"