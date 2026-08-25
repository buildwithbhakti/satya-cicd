import datetime
from unittest import result
from urllib import request

from django.shortcuts import render

# Create your views here
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from teachers.models import Tests, Questions, QuestionOption, MatchItem
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
import json
from .models import Answers, Attempts, Tests, Questions, MatchedPair, SelectedOption, TestLogs
from speech.models import AnswerAudio

from django.utils import translation
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .decorators import student_required
from django.db.models import Q, Max
from django.utils.dateparse import parse_datetime



@student_required
def students_menu_view(request):
    return render(request, "students_menu.html")

@student_required
def active_test_list_view(request):
    # active_tests = Tests.objects.filter(isActive=True,user__institute=request.user.institute, standard=request.user.standard)

    now = datetime.datetime.now()

    active_tests = Tests.objects.filter(
        user__institute=request.user.institute,
        standard__standard=request.user.standard,
    ).filter(
        Q(isActive=True, forPractice=False) |  # show all active tests
        Q(isActive=False, forPractice=False, schedule__date=now.date(), schedule__gte=now)  # show inactive tests only if scheduled today and time has passed
    ).order_by('-isActive', 'schedule')
    
    # Check submission status for each test
    test_data = []
    for test in active_tests:
        attempt = Attempts.objects.filter(user=request.user, test=test).order_by('-attempt_number').first()

        is_tampered = False
        if not test.verify_signature():
            is_tampered = True
    
        test_data.append({
            'test': test,
            'is_submitted': attempt.submitted if attempt else False,
            'attempt_number': attempt.attempt_number if attempt else 0,
            'retake': attempt.retake if attempt else False,
            'is_tampered': is_tampered
        })

    return render(request, "active_test_list.html", {'tests': test_data})


@student_required
def take_test(request, pk):

    test = get_object_or_404(Tests, pk=pk)
    
    if request.method == 'POST':
        answers = Answers.objects.filter(user=request.user, test=test)
        questions = test.questions.all()
        latest_attempt = Attempts.objects.filter(user=request.user, test=test).order_by('-attempt_number').first()
        latest_attempt.submitted = True
        latest_attempt.end_time = timezone.now()
        latest_attempt.save()

        return render(request, 'submit_test.html', {'test': test, 'questions': questions, 'answers': answers})
    else:
        # check if student is allowed to retake for this test and user
        
        if(Attempts.objects.filter(user=request.user, test=test, submitted= True, retake=True).exists()):
            if(Attempts.objects.filter(user=request.user, test=test, submitted= False, retake=False).exists()):
                attempt = Attempts.objects.get(user=request.user, test=test, submitted= False, retake=False)
            elif(Attempts.objects.filter(user=request.user, test=test, submitted= True, retake=False).exists()):
                attempt = Attempts.objects.get(user=request.user, test=test, submitted= True, retake=False)
            else:
                last_attempt = Attempts.objects.filter(user=request.user, test=test).aggregate(Max('attempt_number'))['attempt_number__max']
                attempt = Attempts.objects.create(user=request.user, test=test, attempt_number=(last_attempt or 0) + 1)
        
        elif(Attempts.objects.filter(user=request.user, test=test, submitted= True, retake=False).exists()):
            attempt = Attempts.objects.get(user=request.user, test=test, submitted= True, retake=False)
        else:
            attempt, created = Attempts.objects.get_or_create(user=request.user, test=test, submitted=False, retake=False)

           
        total_duration = attempt.test.time
        elapsed = timezone.now() - attempt.start_time
        remaining = total_duration - elapsed

        # Clamp to 0 if time is already up
        remaining_seconds = max(int(remaining.total_seconds()), 0)

        existing = Answers.objects.filter(user=request.user, test=test)
        answers_by_q = {a.question_id: a for a in existing}

        questions = test.questions.all()
        qa_pairs = []

        if not attempt.submitted or attempt.retake:
            for q in questions:
                qa_pairs.append({
                    'question': q,
                    'answer': answers_by_q.get(q.pk, None)  # full Answer instance or None
                })

    translation.activate(test.medium)
        
    return render(request, 'take_test.html', {'test': test, 'qa_pairs': qa_pairs, 'remaining_seconds': remaining_seconds, 'attempt': attempt})


@student_required
@require_POST
def save_answer_ajax(request):
    # --- Parse & validate input ---
    try:
        data = json.loads(request.body)
        question_id = int(data['question_id'])
        test_id = int(data['test_id'])
        answer = data.get('answer', '').strip()
        audio_filename = data.get('audio_filename', '')
        answer_status = data.get('answer_status', '')
    except (KeyError, ValueError, json.JSONDecodeError):
        return HttpResponseBadRequest('invalid-json')

    # --- Fetch & validate relationships in as few queries as possible ---
    # Single query: get test and prefetch its question IDs
    test = get_object_or_404(
        Tests.objects.prefetch_related('questions'),
        pk=test_id
    )
    question = get_object_or_404(
        Questions.objects.only('pk', 'question_type'),
        pk=question_id
    )

    if not test.questions.filter(pk=question_id).exists():
        return HttpResponseForbidden('question-not-in-test')

    q_type = question.question_type
    selected_option = None
    col_a = col_b = None

    # --- Type-specific answer resolution ---
    if q_type in ('MCQ', 'TF'):
        selected_option = get_object_or_404(QuestionOption.objects.only('pk', 'option_text'), pk=answer)
        answer = selected_option.option_text

    elif q_type == 'MSQ':
        selected_option_for_msq = get_object_or_404(QuestionOption.objects.only('pk'), pk=answer)
        answer = ''

    elif q_type == 'MTF':
        try:
            a_id, b_id = answer.split('_')
        except ValueError:
            return HttpResponseBadRequest('invalid-mtf-answer')

        col_a = get_object_or_404(MatchItem.objects.only('pk', 'label'), pk=a_id)
        col_b = get_object_or_404(MatchItem.objects.only('pk', 'label'), pk=b_id)

        # Build the answer text from existing pairs, replacing the one being updated
        existing_pairs = (
            MatchedPair.objects
            .filter(answer__user=request.user, answer__test=test, answer__question=question)
            .select_related('item_a', 'item_b')
        )
        lines = []
        matched_col_a = False
        for pair in existing_pairs:
            if pair.item_a_id == col_a.id:
                lines.append(f"{col_a.label} => {col_b.label}")
                matched_col_a = True
            else:
                lines.append(str(pair))
        if not matched_col_a:
            lines.append(f"{col_a.label} => {col_b.label}")
        answer = '\n'.join(lines)

    # --- Persist the answer (one upsert) ---
    with transaction.atomic():
        obj, created = Answers.objects.update_or_create(
            user=request.user,
            test=test,
            question=question,
            defaults={'answer': answer, 'status': answer_status, 'option': selected_option},
        )

        if q_type == 'MTF':
            MatchedPair.objects.update_or_create(
                answer=obj,
                item_a=col_a,
                defaults={'item_b': col_b},
            )

        elif q_type == 'MSQ':
            # Toggle: delete if exists, create if not — one query each
            deleted, _ = SelectedOption.objects.filter(answer=obj, option=selected_option_for_msq).delete()
            if not deleted:
                SelectedOption.objects.create(answer=obj, option=selected_option_for_msq)

        if audio_filename:
            AnswerAudio.objects.create(answer=obj, file_name=audio_filename)

    return JsonResponse({'status': 'ok', 'created': created})


@student_required
def submitted_test_list_view(request):
        submitted_attempts = Attempts.objects.filter(user=request.user, submitted=True, retake=False).select_related('test')
        return render(request, "submitted_test_list.html", {'attempts': submitted_attempts})




@csrf_exempt
@student_required
def log_activity_batch(request):
                
        body = request.body.decode("utf-8")
        data = json.loads(body)
        
        # Support both single log and batch logs
        logs = data if isinstance(data, list) else [data]
        
        if not logs:
            return JsonResponse({"status": "error", "message": "No logs"}, status=400)
        
        test_id = logs[0].get("test_id")
        
        if test_id:
            test = Tests.objects.get(id=test_id)
        else:
            test = None
       
        # Get max version once
        latest_version = (
            TestLogs.objects.filter(user=request.user, test=test)
            .aggregate(Max("version"))
            .get("version__max") or 0
        )
        
        # Bulk create
        log_objects = [
            TestLogs(
                user=request.user,
                test=test,
                mode=log.get("mode", "system"),
                type=log.get("type", "info"),
                activity=log.get("activity", ""),
                function=log.get("function_name", ""),
                audio_filename=log.get("audio_filename", ""),
                text=log.get("text", ""),
                page=log.get("page", ""),
                version=latest_version + i + 1,
                timestamp=log.get("timestamp"),
                ip_address = request.META.get("REMOTE_ADDR")
            )
            for i, log in enumerate(logs)
        ]
        
        with transaction.atomic():
            TestLogs.objects.bulk_create(log_objects)
        
        return JsonResponse({"status": "success", "logged": len(log_objects)})
    

@student_required
def practice_test_view(request):
   
    active_tests = Tests.objects.filter(
        user__institute=request.user.institute,
        medium=request.LANGUAGE_CODE,
        standard__standard=request.user.standard,
        forPractice=True
    ).order_by('-updated_at')
    
    
   # Check submission status for each test
    test_data = []
    for test in active_tests:
        attempt = Attempts.objects.filter(user=request.user, test=test).order_by('-attempt_number').first()
    
        test_data.append({
            'test': test,
            'is_submitted': attempt.submitted if attempt else False,
            'attempt_number': attempt.attempt_number if attempt else 0,
            'retake': attempt.retake if attempt else False
        })
    
    return render(request, "active_test_list.html", {'tests': test_data})

@student_required
def check_speech_view(request):
    return render(request, "check_speech.html")