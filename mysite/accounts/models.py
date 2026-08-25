from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random
from django.contrib.auth import get_user_model

class Institute(models.Model):
    name = models.CharField(max_length=200)
    affiliation = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=10, blank=True)
    website = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'


class CustomUser(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ACCOUNT_TYPE_CHOICES = [
        (STUDENT, _('Student')),
        (TEACHER, _('Teacher')),
    ]
    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
        ('other', _('Other')),
    ]
    account_type = models.CharField(max_length=7, choices=ACCOUNT_TYPE_CHOICES, default=STUDENT)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    standard = models.IntegerField(null=True, blank=True)
    institute = models.ForeignKey(Institute, related_name='institute', on_delete=models.CASCADE, null=True, blank=True)

    SPEECH = 'speech'
    KEYBOARD = 'keyboard'
    EXAM_MODE_CHOICES = [
        (SPEECH, _('Speech')),
        (KEYBOARD, _('Keyboard')),
    ]
    exam_mode = models.CharField(max_length=8, choices=EXAM_MODE_CHOICES, default=SPEECH)

class PasswordResetOTP(models.Model):
    user    = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp     = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        # OTP expires after 10 minutes
        expiry = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() < expiry and not self.is_used

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))



class PasswordHistory(models.Model):
    """
    Stores hashed history of previously used passwords for a user.
    Used to prevent password reuse during password changes.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_history'
    )
    password = models.CharField(
        max_length=128,
        help_text="Hashed password value"
    )
    created_at = models.DateTimeField(default=timezone.now)
 
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Password History"
        verbose_name_plural = "Password Histories"
 
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
 