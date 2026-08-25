from django.shortcuts import render

# Create your views here
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from teachers.models import Tests, Questions, QuestionOption, MatchItem
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
import json
from .models import Answers, Tests, Questions, MatchedPair, SelectedOption
from speech.models import AnswerAudio

from django.utils import translation

@login_required
def students_menu_view(request):
    return render(request, "students_menu.html")

@login_required
def active_test_list_view(request):
    # test = get_object_or_404(Tests, user = request.user.standard == )
    active_tests = Tests.objects.filter(isActive=True,user__institute=request.user.institute, standard=request.user.standard)


    return render(request, "active_test_list.html", {'tests': active_tests})


@login_required
def take_test(request, pk):

    test = get_object_or_404(Tests, pk=pk)
    
    if request.method == 'POST':
        answers = Answers.objects.filter(user=request.user, test=test)
        questions = test.questions.all()
        return render(request, 'submit_test.html', {'test': test, 'questions': questions, 'answers': answers})
    else: 
        existing = Answers.objects.filter(user=request.user, test=test)
        answers_by_q = {a.question_id: a for a in existing}

        questions = test.questions.all()
        qa_pairs = []
        for q in questions:
            qa_pairs.append({
                'question': q,
                'answer': answers_by_q.get(q.pk, None)  # full Answer instance or None
            })

    translation.activate(test.medium)
        
    return render(request, 'take_test.html', {'test': test, 'qa_pairs': qa_pairs})


@login_required
@require_POST
def save_answer_ajax(request):
    # Expect JSON body
    try:
        data = json.loads(request.body.decode('utf-8'))
        question_id = int(data.get('question_id'))
        test_id = int(data.get('test_id'))
        answer = data.get('answer', '').strip()
        audio_filename = data.get('audio_filename', '')
        answer_status = data.get('answer_status', '')

    except Exception:
        return HttpResponseBadRequest('invalid-json')

    # Basic validation
    test = get_object_or_404(Tests, pk=test_id)
    question = get_object_or_404(Questions, pk=question_id)

    # Ensure question belongs to this test (adjust according to your relation)
    if not test.questions.filter(pk=question.pk).exists():
        return HttpResponseForbidden('question-not-in-test')
    
    if question.question_type == "MCQ" or question.question_type == "TF":  
        selected_option = get_object_or_404(QuestionOption, pk=answer)     
        answer = selected_option.option_text
    
    if question.question_type == "MSQ":
        selected_option = get_object_or_404(QuestionOption, pk=answer)
        answer = ""

    elif question.question_type == "MTF":
        col_ab = answer.split("_")
        col_a = get_object_or_404(MatchItem, pk=col_ab[0])
        col_b = get_object_or_404(MatchItem, pk=col_ab[1])
        answer = ""
        pairs_values = MatchedPair.objects.filter(answer__in=Answers.objects.filter(user=request.user, test=test, question=question))
        
        for pair_value in pairs_values:
            if col_a.id == pair_value.item_a.id:
                answer += col_a.label + " => " + col_b.label + "\n"
            else:
                answer += str(pair_value) + "\n"
      
        selected_option = None
    else:
        selected_option = None

    obj, created = Answers.objects.update_or_create(
        user=request.user,
        test=test,
        question=question,
        defaults={'answer': answer, 'status': answer_status, 'option': selected_option}
    )
    # created = "false"
  
    if question.question_type == "MTF":
         MatchedPair.objects.update_or_create(
                    answer = obj,
                    item_a = col_a,                    
                    defaults={'item_b': col_b}
                )
    
    if question.question_type == "MSQ":
        exists = SelectedOption.objects.filter(answer=obj, option = selected_option).exists()
        if exists:
            SelectedOption.objects.get(answer=obj, option = selected_option).delete()
        else:
            SelectedOption.objects.update_or_create(answer=obj, option = selected_option)

    if(audio_filename != ""):
        AnswerAudio.objects.create(
            answer = obj,
            file_name = audio_filename 
        )

    return JsonResponse({'status': 'ok', 'created': created})