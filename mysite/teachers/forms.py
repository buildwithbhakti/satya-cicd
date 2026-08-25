from django import forms

from accounts.utils.sanitizer import SanitizeForm
from .models import Standard, Subject, Tests, Questions, QuestionPaperUpload
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _ 
import regex

validator_msg = _("No special characters allowed")


special_char_validator = RegexValidator(
    regex=regex.compile(r'\A[\w.,\- \n]+\Z', regex.UNICODE),
        message=validator_msg,
        code='invalid_format'
    )

question_validator = RegexValidator(
    regex=regex.compile(
        r"\A[\w.,?:\- \n\p{Mn}\p{Mc}\(\)/\'\";!]+\Z",
        regex.UNICODE
    ),
    message=validator_msg,
    code="invalid_format"
)

class TestsForm(SanitizeForm, forms.ModelForm):
    class Meta:
        model = Tests
        fields = ['subject', "total_marks",'time', "medium", "standard", "name", "instructions", "isActive", "is_shuffled", "schedule", "forPractice", "tts_model", "asr_model"]
        widgets = {
            'time': forms.TimeInput(format='%H:%M:%S', attrs={'placeholder': 'HH:MM:SS'}),
        }

    name = forms.CharField(validators=[special_char_validator])

    instructions = forms.CharField(validators=[question_validator], required=False,)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
       
        # Set initial queryset for standard
        self.fields['standard'].queryset =  Standard.objects.filter(institute=user.institute).order_by('standard')
        self.fields['standard'].empty_label = "Select Standard"

         # If standard is selected, filter subjects
        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
                self.fields['subject'].queryset = Subject.objects.filter(
                    standards__id=standard_id
                ).order_by('name')
            except (ValueError, TypeError):
                self.fields['subject'].queryset = Subject.objects.none()
        elif self.instance.pk and self.instance.standard:
            self.fields['subject'].queryset = self.instance.standard.subjects.all().order_by('name')
        else:
            self.fields['subject'].queryset = Subject.objects.none()
        
        self.fields['subject'].empty_label = "Select Subject"
    
    def clean(self):
        cleaned_data = super().clean()
        standard = cleaned_data.get('standard')
        subject = cleaned_data.get('subject')
        
        if standard and subject:
            if not standard.subjects.filter(id=subject.id).exists():
                raise forms.ValidationError(
                    f"Subject '{subject.name}' is not available for Standard {standard.standard}."
                )
        
        return cleaned_data
    
    

class QuestionsForm(SanitizeForm, forms.ModelForm):
    class Meta:
        model = Questions
        fields = ['question_type', 'question', "marks", "min_words", "max_words", "order", 'image', 'image_description', 'is_shuffled']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 2}),
            'order': forms.NumberInput(attrs={'min': 0}),
            'max_words': forms.NumberInput(attrs={'min': 0}),
            'min_words': forms.NumberInput(attrs={'min': 0}),
        }

    question = forms.CharField(validators=[question_validator], required=True,)
    image_description = forms.CharField(validators=[question_validator], required=False,)

    
class QuestionPaperUploadForm(forms.ModelForm):
    class Meta:
        model = QuestionPaperUpload
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data['file']
        valid_types = [
            'application/pdf',
            'image/jpeg', 'image/png', 'image/jpg',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
        ]
        if file.content_type not in valid_types:
            raise forms.ValidationError("Only PDF, JPG, PNG, DOC, and DOCX files are allowed.")
        if file.size > 15 * 1024 * 1024:
            raise forms.ValidationError("File too large (max 15MB).")
        return file