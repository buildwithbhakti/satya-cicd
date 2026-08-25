
from django import forms

from accounts.utils.sanitizer import SanitizeForm
from .models import Answers

class AnswersForm(SanitizeForm, forms.ModelForm):
     class Meta:
        model = Answers
        fields = ["answer", "status", "marks"]
