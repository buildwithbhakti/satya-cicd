from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm, InstituteForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from teachers.decorators import teacher_required
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
# from .models import  CustomUser
from .models import CustomUser, Institute, PasswordResetOTP
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.utils.password_validators import PasswordHistoryValidator


from .forms import HistoryAwarePasswordChangeForm
from accounts.utils.password_validators import save_password_to_history

@ratelimit(key='ip', rate='10/m', block=True)
def register_view(request):
    institutes = Institute.objects.filter(is_active=True)
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            if request.user.is_authenticated:
                # registering a student by an admin/teacher, so activate immediately
                user.is_active = True
                messages.success(request, _("Registration successful! Student can now login."))
            else:
                user.is_active = False
                messages.success(request, _("Registration successful! But you can only login once approved by an admin/teacher."))
 
            user.save()
            save_password_to_history(user) 
            # if request.user.is_anonymous:
            #     login(request, user)
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form, "institutes": institutes})

@ratelimit(key='ip', rate='10/m', block=True)
def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session['show_welcome'] = True
            return redirect("index") 
    else:
        form = CustomAuthenticationForm()
    
    if request.user.is_authenticated:
        return redirect("index")
    else:    
        return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

@ratelimit(key='ip', rate='10/m', block=True)
def register_institute_view(request):
    if request.method == "POST":
        form = InstituteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your request to has been submitted. It will be reviewed by an admin. After approval, it will be available for selection."))
            return redirect("register")       
    else:
        form = InstituteForm()
    return render(request, "register_institute.html", {"form": form})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated."))
            return redirect("index")
        else:
            messages.error(request, _("Something went wrong. Please check the form for errors."))
            print(form.errors) 
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "profile_edit.html", {"form": form})

@teacher_required
def profile_edit_student(request, student_id):
    student = CustomUser.objects.get(pk=student_id)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated."))
            return redirect("student_list")
    else:
        form = ProfileUpdateForm(instance=student)
    return render(request, "profile_edit.html", {"form": form})


@teacher_required
def profile_delete(request, student_id):
    student = get_object_or_404(CustomUser, pk=student_id)
    if request.method == 'POST':
        student.delete()
        messages.success(request, _("Profile deleted."))
        return redirect('student_list')

@csrf_exempt
@teacher_required
@require_POST 
def student_toggle(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        student_id = data.get('student_id')
        is_active = data.get('isActive')

        student = get_object_or_404(CustomUser, pk=student_id)
        student.is_active = is_active
        student.save()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@ratelimit(key='ip', rate='10/m', block=True)
def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        email    = request.POST.get('email').strip()

        # Step 1 — Check if username exists
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            messages.error(request, _('No account found with this username.'))
            return render(request, 'forgot_password.html')

        # Step 2 — Check if email matches the username
        if user.email.lower() != email.lower():
            messages.error(request, _('The email address does not match our records for this username.'))
            return render(request, 'forgot_password.html')

        # Step 3 — All good, generate and send OTP
        PasswordResetOTP.objects.filter(user=user).delete()  # clear old OTPs

        otp = PasswordResetOTP.generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            subject='Your Password Reset OTP',
            message=f'Hi {user.first_name} {user.last_name},\n\nYour OTP for password reset is: {otp}\n\nThis OTP expires in 10 minutes.\n\nIf you did not request this, ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        request.session['reset_email'] = email
        # messages.success(request, f'OTP sent to {email}.')
        messages.success(request, _("OTP sent to %(email)s.") % {'email': email})
        return redirect('verify_otp')

    return render(request, 'forgot_password.html')

@ratelimit(key='ip', rate='10/m', block=True)
def verify_otp(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            user = CustomUser.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(
                user=user, otp=entered_otp, is_used=False
            ).latest('created_at')

            if otp_record.is_valid():
                otp_record.is_used = True
                otp_record.save()
                request.session['otp_verified_email'] = email
                return redirect('reset_password')
            else:
                messages.error(request, _('OTP has expired. Please request a new one.'))
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, _('Invalid OTP. Please try again.'))

    return render(request, 'verify_otp.html')

# @ratelimit(key='ip', rate='10/m', block=True)
# def reset_password(request):
#     email = request.session.get('otp_verified_email')
#     if not email:
#         return redirect('forgot_password')

#     if request.method == 'POST':
#         password1 = request.POST.get('password1')
#         password2 = request.POST.get('password2')

#         if password1 != password2:
#             messages.error(request, _('Passwords do not match.'))
#             return render(request, 'reset_password.html')

#         if len(password1) < 8:
#             messages.error(request, _('Password must be at least 8 characters.'))
#             return render(request, 'reset_password.html')

#         user = CustomUser.objects.get(email=email)
#         user.set_password(password1)
#         user.save()

#         # Clear session
#         del request.session['otp_verified_email']
#         request.session.pop('reset_email', None)

#         messages.success(request, _('Password reset successful. Please log in.'))
#         return redirect('login')

#     return render(request, 'reset_password.html')


def reset_password(request):
    email = request.session.get('otp_verified_email')
    if not email:
        return redirect('forgot_password')
 
    if request.method == 'POST':
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
 
        if password1 != password2:
            messages.error(request, _('Passwords do not match.'))
            return render(request, 'reset_password.html')
 
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, _('No account found. Please restart the process.'))
            return redirect('forgot_password')
 
        # Runs ALL validators in AUTH_PASSWORD_VALIDATORS, including
        # MinimumLengthValidator, CommonPasswordValidator, and
        # PasswordHistoryValidator — no manual checks needed.
        try:
            validate_password(password1, user=user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'reset_password.html')
 
        save_password_to_history(user)
        user.set_password(password1)
        user.save()
 
        request.session.pop('otp_verified_email', None)
        request.session.pop('reset_email', None)
 
        messages.success(request, _('Password reset successful. Please log in.'))
        return redirect('login')
 
    return render(request, 'reset_password.html')

# def reset_password(request):
#     email = request.session.get('otp_verified_email')
#     if not email:
#         return redirect('forgot_password')
 
#     if request.method == 'POST':
#         password1 = request.POST.get('password1', '').strip()
#         password2 = request.POST.get('password2', '').strip()
 
#         # ── Basic validations ──────────────────────────────────────────────
#         if password1 != password2:
#             messages.error(request, _('Passwords do not match.'))
#             return render(request, 'reset_password.html')
 
#         if len(password1) < 12:
#             messages.error(request, _('Password must be at least 8 characters.'))
#             return render(request, 'reset_password.html')
 
#         # ── Fetch user ─────────────────────────────────────────────────────
#         try:
#             user = CustomUser.objects.get(email=email)
#         except CustomUser.DoesNotExist:
#             messages.error(request, _('No account found. Please restart the process.'))
#             return redirect('forgot_password')
 
#         # ── Password history check ─────────────────────────────────────────
#         # Rejects the new password if it matches any of the last N used passwords.
#         validator = PasswordHistoryValidator()
#         try:
#             validator.validate(password1, user=user)
#         except Exception as e:
#             # ValidationError message is user-friendly; surface it directly.
#             messages.error(request, str(e).strip("['']"))
#             return render(request, 'reset_password.html')
 
#         # ── Save old password to history BEFORE overwriting ────────────────
#         # Must happen before set_password() so the current hash is captured.
#         save_password_to_history(user)
 
#         # ── Commit new password ────────────────────────────────────────────
#         user.set_password(password1)
#         user.save()
 
#         # ── Clear OTP session keys ─────────────────────────────────────────
#         request.session.pop('otp_verified_email', None)
#         request.session.pop('reset_email', None)
 
#         messages.success(request, _('Password reset successful. Please log in.'))
#         return redirect('login')
 
#     return render(request, 'reset_password.html')



@login_required
def change_password_view(request):
    """
    Password change view that:
    1. Validates the new password is not in recent history
    2. Saves the old password to history before updating
    3. Keeps the user logged in after a successful change
    """
    form = HistoryAwarePasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = request.user

        # Save the current password to history BEFORE it is overwritten
        save_password_to_history(user)

        # Save the new password (this overwrites user.password)
        form.save()

        # Keep the user's session alive after the password change
        update_session_auth_hash(request, user)

        messages.success(
            request,
            "Your password has been updated successfully."
        )
        return redirect('password_change_done')

    return render(request, 'password_change.html', {'form': form})