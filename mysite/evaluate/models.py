from django.db import models
from evaluate.utils.hash import compute_signature
from students.models import Answers, Attempts
from accounts.models import CustomUser
from auditlog.registry import auditlog

# Create your models here.
class Evaluation(models.Model):
    answer = models.ForeignKey(Answers, related_name='evaluate_answer', on_delete=models.CASCADE)
    evaluator = models.ForeignKey(CustomUser, related_name='evaluator', on_delete=models.CASCADE)
    marks = models.IntegerField(blank=True, null=True)
    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.answer} - '

auditlog.register(Evaluation)


class Result(compute_signature, models.Model):
    attempt = models.ForeignKey(Attempts, related_name='test_result', on_delete=models.CASCADE)
    marks_obtained = models.IntegerField(blank=True, null=True)
    evaluator = models.ForeignKey(CustomUser, related_name='test_evaluator', on_delete=models.CASCADE)
    remarks = models.TextField(blank=True)
    is_passed = models.BooleanField(default=False)

    signature = models.CharField(max_length=64, editable=False, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.attempt.user} - {self.marks_obtained}'
    
    SIGNABLE_FIELDS = ['attempt', 'marks_obtained', 'is_passed', 'evaluator']

    
auditlog.register(Result)

