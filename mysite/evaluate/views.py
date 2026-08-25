from django.shortcuts import render
from teachers.models import Tests, Questions
from students.models import Answers
from teachers.views import get_standard_and_test
from accounts.models import CustomUser
from django.shortcuts import get_object_or_404, redirect
from teachers.decorators import teacher_required
from students.decorators import student_required
from django.views.decorators.http import require_POST
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Evaluation, Result
from students.models import Attempts, TestLogs
from django.contrib import messages

from django.db.models import Max
from django.urls import reverse

# @csrf_exempt
# @teacher_required
# def evaluate_test_list_view(request):
#     standards, selected_standard, selected_standard_raw, available_subjects, selected_subject, base_test = get_standard_and_test(request)

#     tests = []
#     if selected_standard is not None and selected_subject:
#         tests = list(
#             Tests.objects.filter(standard__standard=selected_standard, subject__name=selected_subject, isActive=False, readOnly=True ).order_by('-created_at')
#             # Tests.objects.filter(standard=selected_standard, subject=selected_subject).order_by('-created_at')
#         )

#     return render(request, 'eval_test_list.html', {
#         'standards': standards,
#         'available_subjects': available_subjects,
#         'selected_standard': selected_standard_raw,
#         'selected_subject': selected_subject,
#         'tests': tests,
#     })

@teacher_required
def evaluate_test_list_view(request):
    standards, selected_standard_raw, selected_subject_id, selected_subject_name, tests = get_standard_and_test(request)

    if(selected_standard_raw and selected_subject_id):
        tests = list(tests.filter(isActive=False, readOnly=True) | tests.filter(forPractice=True))

    return render(request, 'eval_test_list.html', {
        'standards': standards,
        'selected_standard': selected_standard_raw,
        'selected_subject_id': selected_subject_id,
        'selected_subject_name': selected_subject_name,
        'tests': tests,
    })

@teacher_required
def students_list_evaluate(request, test_id):

    test = get_object_or_404(Tests, pk=test_id)
    attempt_info = Attempts.objects.filter(test=test_id, submitted=True, retake=False).select_related('user').annotate(latest_attempt=Max('attempt_number'))
  
    return render(request, 'students_list_evaluate.html', {'attempts': attempt_info, 'test' : test})

@teacher_required
def student_evaluate(request, test_id, student_id, attempt_id):
    test = get_object_or_404(Tests, pk=test_id)
    student = get_object_or_404(CustomUser, pk=student_id)

    existing = Answers.objects.filter(user=student, test=test)
    answers_by_q = {a.question_id: a for a in existing}

    questions = test.questions.all()
    qa_pairs = []
    for q in questions:
        qa_pairs.append({
            'question': q,
            'answer': answers_by_q.get(q.pk, None)  # full Answer instance or None
        })
       
        
    return render(request, 'student_evaluate.html', {'test' : test,  "student" : student,'qa_pairs': qa_pairs, 'answers':existing, 'attempt_id': attempt_id                         })


@teacher_required
def student_retake(request, test_id, student_id, attempt_id):

    # test = get_object_or_404(Tests, pk=test_id)
    # student = get_object_or_404(CustomUser, pk=student_id)
    attempt = get_object_or_404(Attempts, pk=attempt_id)

    # attempt = Attempts.objects.filter( test=test, user=student, submitted=True, retake=False).order_by('-attempt_number').first()
    attempt.retake = True
    attempt.save()  
    
    return redirect('students_list_evaluate', test_id=test_id)


@student_required
def student_practice_retake(request, test_id, student_id, attempt_id):

    test = get_object_or_404(Tests, pk=test_id, forPractice = True)
    student = get_object_or_404(CustomUser, pk=student_id)
    attempt = get_object_or_404(Attempts, pk=attempt_id)

    # attempt = Attempts.objects.filter( test=test, user=student, submitted=True, retake=False).order_by('-attempt_number').first()
    attempt.retake = True
    attempt.save()
    Answers.objects.filter(test=test, user=student).delete()

    messages.success(request, "You can re-take the test")



    return redirect('students_menu')


@csrf_exempt
@teacher_required
@require_POST
def save_marks(request):
    try:
        data = json.loads(request.body)
        print(f"Received data for saving marks: {data}")
        ansewer_id = data.get('answer_id')
        marks = data.get('marks')
        remarks = data.get('remarks')

        # basic validation
        if marks is None or marks == '':
            return JsonResponse({'error': 'Marks required'}, status=400)
        marks = float(marks)  # or int()
        # optional: validate range
        if marks < 0:
            return JsonResponse({'error': 'Marks must be non-negative'}, status=400)

        answer = get_object_or_404(Answers, pk=ansewer_id)

        # create or update mark record
        mark_obj, created = Evaluation.objects.update_or_create(
            answer=answer, evaluator=request.user,
            defaults={'marks': marks, 'remarks':remarks}
        )
        return JsonResponse({'success': True, 'marks_id': mark_obj.id})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@teacher_required
def view_test_logs(request, test_id, student_id):
    
    try:
        user = CustomUser.objects.get(id=student_id)
        test = Tests.objects.get(id=test_id)
    except (CustomUser.DoesNotExist, Tests.DoesNotExist):
        return render(request, 'partials/logs_error.html', {
            'error': 'User or Test not found'
        })
    
    # Get filter parameters from GET request
    log_type = request.GET.get('type', '').strip()
    log_mode = request.GET.get('mode', '').strip()
    
    # Start with base queryset
    logs = TestLogs.objects.filter(
        user=user,
        test=test
    )
    
    # Apply filters if provided
    if log_type:
        logs = logs.filter(type=log_type)
    if log_mode:
        logs = logs.filter(mode=log_mode)
    
    # Order by timestamp (chronological)
    logs = logs.order_by('timestamp').select_related('user', 'test')
    
    context = {
        'logs': logs,
        'user': user,
        'test': test,
        'type_choices': TestLogs.TYPE_CHOICES,
        'mode_choices': TestLogs.MODE_CHOICES,
        'selected_type': log_type,
        'selected_mode': log_mode,
    }
    
    return render(request, 'partials/test_logs_table.html', context)

@csrf_exempt
@teacher_required
def save_result(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"Received data for saving result: {data}")
            attempt_id = data.get('attempt_id')
            marks_obtained = data.get('marks_obtained')
            remarks = data.get('remarks')
            is_passed =bool(data.get('passed'))
            test_id = data.get('test_id')

            attempt = get_object_or_404(Attempts, pk=attempt_id, submitted=True)
            attempt.evaluated = True
            attempt.save()

            result_obj, created = Result.objects.update_or_create(
                attempt=attempt,
                defaults={
                    'marks_obtained': marks_obtained,
                    'remarks': remarks,
                    'is_passed': is_passed,
                    'evaluator': request.user
                }
            )

            if created:
                result_obj.signature = result_obj.generate_signature()
                result_obj.save(update_fields=['signature'])

            # return JsonResponse({'success': True, 'result_id': result_obj.id})
            url = reverse('students_list_evaluate', kwargs={'test_id': test_id})
            return JsonResponse({'redirect': url})

            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error saving result: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return HttpResponseBadRequest('Invalid request method') 
    
@teacher_required
def view_student_result(request, test_id, student_id, attempt_id):
    attempt = get_object_or_404(Attempts, pk=attempt_id, user__id=student_id, test__id=test_id)

    result = Result.objects.filter(attempt=attempt).first()

    is_tampered = False
    if not result.verify_signature():
        is_tampered = True
    

    test = get_object_or_404(Tests, pk=test_id)
    student = get_object_or_404(CustomUser, pk=student_id)

    existing = Answers.objects.filter(user=student, test=test)
    answers_by_q = {a.question_id: a for a in existing}

    questions = test.questions.all()
    qa_pairs = []
    for q in questions:
        qa_pairs.append({
            'question': q,
            'answer': answers_by_q.get(q.pk, None),  # full Answer instance or None
            'evaluation': Evaluation.objects.filter(answer__question=q, answer__user=student).first()   
        })
       
        
    return render(request, 'student_result.html', {'test' : test,  "student" : student,'qa_pairs': qa_pairs, 'answers':existing, 'attempt': attempt, 'result': result, 'is_tampered': is_tampered })
