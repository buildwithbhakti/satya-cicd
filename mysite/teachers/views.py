from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponseBadRequest, FileResponse, StreamingHttpResponse
from django.db.models.functions import Coalesce
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max
from django.contrib import messages
from django_q.tasks import schedule
from django_q.models import Schedule

from .models import QuestionPaperUpload, Subject, TestEvent, Tests, Questions, QuestionOption, MatchItem, MatchPair, Standard
from .forms import TestsForm, QuestionsForm, QuestionPaperUploadForm
from .decorators import teacher_required
from .sse_store import broadcast
from .utils import extract_text_from_file, parse_questions_with_ai
from accounts.models import CustomUser

import json, os, datetime, time, regex

@teacher_required
def teachers_menu_view(request):
    if request.session.pop('show_welcome', False):
        show_welcome = True
    else:
        show_welcome = False
    return render(request, "teachers_menu.html", {"show_welcome": show_welcome})

@teacher_required
def test_create(request):
    if request.method == 'POST':
        form = TestsForm(request.POST, user=request.user)
        if form.is_valid():
            test = form.save(commit=False)
            test.user = request.user
            
            # Extra safety check
            if test.schedule and test.schedule <= datetime.datetime.now():
                form.add_error('schedule', 'Scheduled time must be in the future.')
                return render(request, 'test_create.html', {'form': form})

            # check if test with same name, subject and standard already exists for this institute 
            if Tests.objects.filter(user__institute=request.user.institute, name=test.name, subject=test.subject, standard=test.standard).exists():
                form.add_error('name', 'Test with this name already exists.')
                return render(request, 'test_create.html', {'form': form})

            test.save()

            # Cancel any existing schedules for safety
            Schedule.objects.filter(name__in=[
                f'activate-test-{test.pk}',
                f'deactivate-test-{test.pk}'
            ]).delete()

            if test.schedule:
                # Auto-activate at scheduled time
                # deactivation will be chained inside activate_test()
                schedule(
                    'teachers.tasks.activate_test',
                    test.pk,
                    schedule_type=Schedule.ONCE,
                    next_run=test.schedule,
                    name=f'activate-test-{test.pk}',
                )
            
            return redirect('test_questions', pk=test.pk)
    else:
        form = TestsForm(user=request.user)
    return render(request, 'test_create.html', {'form': form})

@teacher_required
def get_subjects_by_standard(request):
    standard_id = request.GET.get('standard_id')
   
    if standard_id:
        subjects = Subject.objects.filter(
            standards__id=standard_id
        ).order_by('name').values('id', 'name')
        return JsonResponse({'subjects': list(subjects)})
    return JsonResponse({'subjects': []})

# def subjects_by_standard(request):
#     standard_id = request.GET.get('standard_id')
#     subjects = []
#     if standard_id:
#         try:
#             subject_ids = (
#                 Tests.objects.filter(
#                     user__institute=request.user.institute,
#                     standard__standard=int(standard_id)
#                 )
#                 .values_list('subject', flat=True)
#                 .distinct()
#             )
#             subjects = list(
#                 Subject.objects.filter(id__in=subject_ids)
#                 .values('id', 'name')
#                 .order_by('name')
#             )
#         except (ValueError, TypeError):
#             pass
#     return JsonResponse({'subjects': subjects})

@teacher_required
def get_standard_and_test(request, selected_standard_id = None, selected_subject_id = None):
    # base_tests = Tests.objects.filter(
    #     user__institute=request.user.institute
    # ).order_by('standard__standard', 'subject__name')

    # standards = Standard.objects.filter(
    #     id__in=base_tests.values_list('standard', flat=True).distinct()
    # ).order_by('standard')

    standards = Standard.objects.filter(institute=request.user.institute).order_by('standard')

    if( not selected_standard_id and not selected_subject_id):
        selected_standard_id = request.GET.get('standard', '').strip()
        selected_subject_id = request.GET.get('subject', '').strip()
        # selected_standard_id = None
    
    tests =[]
    selected_subject_name = ''

    if selected_standard_id and selected_subject_id:
        try:
            subject_obj = Subject.objects.get(id=selected_subject_id)
            selected_subject_name = subject_obj.name
            tests = Tests.objects.filter(
                standard_id=int(selected_standard_id),  # direct PK lookup
                subject=subject_obj, user__institute=request.user.institute
            ).order_by('-created_at')
        except (Subject.DoesNotExist, ValueError, TypeError):
            tests = []

    return standards, str(selected_standard_id), selected_subject_id, selected_subject_name, tests

# def get_standard_and_test(request):
#     base_tests = Tests.objects.filter(
#         user__institute=request.user.institute
#     ).order_by('standard__standard', 'subject__name')

#     # Get distinct standard objects and extract their 'standard' field values
#     standards = sorted(
#         set(
#             base_tests.values_list('standard__standard', flat=True)
#             .distinct()
#         )
#     )

#     selected_standard_raw = request.POST.get('standard') or ''
#     selected_subject = (request.POST.get('subject') or '').strip()
#     selected_standard = None

    
#     if selected_standard_raw:
#         try:
#             selected_standard = int(selected_standard_raw)
#         except (TypeError, ValueError):
#             selected_standard = None
#             selected_standard_raw = ''

#     # If standard is not selected, there should not be any item in subject.
#     available_subjects = []
#     if selected_standard is not None:
        
#         # Get subject IDs
#         subject_ids = (
#             base_tests.filter(standard__standard=selected_standard)
#             .values_list('subject', flat=True)
#             .distinct()
#         )
        
#         # Fetch subjects - modeltranslation automatically returns translated 'name'
#         available_subjects = sorted(
#             Subject.objects.filter(id__in=subject_ids)
#             .values_list('name', flat=True)
#         )


#     return standards, selected_standard, selected_standard_raw, available_subjects, selected_subject, base_tests

# @teacher_required
# @csrf_exempt
# def test_list(request):

#     standards, selected_standard, selected_standard_raw, available_subjects, selected_subject, base_tests = get_standard_and_test(request)

#     tests = []
#     if selected_standard is not None and selected_subject:
        
#         # Get the subject object matching the translated name
#         try:
#             subject_obj = Subject.objects.get(name=selected_subject)
            
#             tests = base_tests.filter(
#                 standard__standard=selected_standard,
#                 subject=subject_obj,
#             ).order_by('-created_at')
#         except Subject.DoesNotExist:
#             tests = []

#     return render(request, 'test_list.html', {
#         'standards': standards,
#         'available_subjects': available_subjects,
#         'selected_standard': selected_standard_raw,
#         'selected_subject': selected_subject,
#         'tests': tests,
#     })

@teacher_required
def test_list(request):
    standards, selected_standard_raw, selected_subject_id, selected_subject_name, tests = get_standard_and_test(request)

    if not tests:
        if selected_standard_raw:
            tests = Tests.objects.filter(user__institute=request.user.institute,standard=int(selected_standard_raw), isActive = True ).order_by('standard')
        else:
            tests = Tests.objects.filter(user__institute=request.user.institute, isActive = True ).order_by('standard')

    return render(request, 'test_list.html', {
        'standards': standards,
        'selected_standard': selected_standard_raw,
        'selected_subject_id': selected_subject_id,
        'selected_subject_name': selected_subject_name,
        'tests': tests,
    })


# @teacher_required
# def test_list_active(request):
#     standards, selected_standard_raw, selected_subject_id, selected_subject_name, tests = get_standard_and_test(request)

#     if not tests:
#         tests = Tests.objects.filter(user__institute=request.user.institute, isActive = True ).order_by('standard')

#     return render(request, 'test_list.html', {
#         'standards': standards,
#         'selected_standard': selected_standard_raw,
#         'selected_subject_id': selected_subject_id,
#         'selected_subject_name': selected_subject_name,
#         'tests': tests,
#     })


@teacher_required
def test_view(request, test_id):
    standard_id = request.GET.get('standard')
    test = Tests.objects.get(id = test_id )

    if standard_id:
        standards, selected_standard_id, selected_subject_id, selected_subject_name, tests = get_standard_and_test(request)

    else:
        selected_standard_id = test.standard_id
        selected_subject_id = test.subject_id
        standards, selected_standard_id, selected_subject_id, selected_subject_name, tests = get_standard_and_test(request, selected_standard_id, selected_subject_id)
        
    return render(request, 'test_list.html', {
        'standards': standards,
        'selected_standard': str(selected_standard_id),
        'selected_subject_id': selected_subject_id,
        'selected_subject_name': selected_subject_name,
        'tests': tests,
        'test_id' : test.id,
    })


# @teacher_required
# def test_list_active(request):
#     tests = Tests.objects.filter(user__institute=request.user.institute, isActive = True ).order_by('standard')

#     standards, selected_standard, selected_standard_raw, available_subjects, selected_subject, base_tests = get_standard_and_test(request)
 
#     return render(request, 'test_list.html', {
#         'standards': standards,
#         'available_subjects': available_subjects,
#         'selected_standard': selected_standard_raw,
#         'selected_subject': selected_subject,
#         'tests': tests,
#     })

@teacher_required
def test_delete(request, pk):
    test = get_object_or_404(Tests, pk=pk, user = request.user)
    if request.method == 'POST':
        test.delete()
        messages.success(request, "Test deleted")
        return redirect('test_list')
    
@teacher_required
def test_edit(request, pk):
    test = get_object_or_404(Tests, pk=pk, user = request.user, isActive=False, readOnly=False)
    if request.method == 'POST':
        form = TestsForm(request.POST, instance=test, user=request.user)
        if form.is_valid():

             # Extra safety check
            if test.schedule and test.schedule <= datetime.datetime.now():
                form.add_error('schedule', 'Scheduled time must be in the future.')
                return render(request, 'test_create.html', {'form': form})
            
            form.save()
            # Cancel any existing schedules for safety
            Schedule.objects.filter(name__in=[
                f'activate-test-{test.pk}',
                f'deactivate-test-{test.pk}'
            ]).delete()

            if test.schedule:
                # Auto-activate at scheduled time
                # deactivation will be chained inside activate_test()
                schedule(
                    'teachers.tasks.activate_test',
                    test.pk,
                    schedule_type=Schedule.ONCE,
                    next_run=test.schedule,
                    name=f'activate-test-{test.pk}',
                )

            return redirect('test_questions', pk=test.pk)
    else:
        form = TestsForm(instance=test, user=request.user)
    return render(request, 'test_create.html', {'form': form, 'editing': True, 'test': test})


@teacher_required
def test_questions(request, pk):
    test = get_object_or_404(Tests, pk=pk,  user = request.user, isActive=False, readOnly=False)
    questions = test.questions.all().order_by('order')
    # Exclude questions that are already in this test (including ones previously added from bank).
    current_bank_root_ids = list(
        test.questions.annotate(root_id=Coalesce('bank_source_question_id', 'id'))
        .values_list('root_id', flat=True)
    )

    bank_questions = Questions.objects.filter(
        test__user__institute=request.user.institute,
        test__standard=test.standard,
        test__subject=test.subject,
    ).exclude(test=test).annotate(
        root_id=Coalesce('bank_source_question_id', 'id')
    ).exclude(
        root_id__in=current_bank_root_ids
    ).select_related('test').order_by('test__name', 'order')
    form = QuestionsForm()
    question_paper_upload = QuestionPaperUpload.objects.filter(test=test, user=request.user).order_by('-uploaded_at').first()
    return render(request, 'test_questions.html', {
        'test': test,
        'questions': questions,
        'bank_questions': bank_questions,
        'form': form,
        'extracted_text': question_paper_upload.extracted_text if question_paper_upload else '',
    })


@teacher_required
@transaction.atomic
@require_POST
def question_import_from_bank(request, pk):
    test = get_object_or_404(Tests, pk=pk, user=request.user)

    source_question_ids = request.POST.getlist('source_question_ids[]') or []
    # Back-compat with single-select payload.
    if not source_question_ids:
        single_id = request.POST.get('source_question_id')
        if single_id:
            source_question_ids = [single_id]

    if not source_question_ids:
        return HttpResponseBadRequest("source_question_ids[] (or source_question_id) is required")

    sources = list(
        Questions.objects.select_related('test', 'test__user', 'bank_source_question').prefetch_related(
            'options',
            'match_items',
            'match_pairs__item_a',
            'match_pairs__item_b',
        ).filter(pk__in=source_question_ids)
    )

    if not sources:
        return HttpResponseBadRequest("No valid source questions found")

    # Root ids already present in this test (avoid duplicates)
    existing_root_ids = set(
        test.questions.annotate(root_id=Coalesce('bank_source_question_id', 'id'))
        .values_list('root_id', flat=True)
    )

    next_order = (test.questions.aggregate(m=Max('order')).get('m') or 0) + 1
    added = 0

    for source_question in sources:
        # Safety checks: same institute + same standard/subject
        if source_question.test.user.institute != request.user.institute:
            continue
        if source_question.test.standard != test.standard or source_question.test.subject != test.subject:
            continue

        root = source_question.bank_source_question or source_question
        if root.id in existing_root_ids:
            continue

        new_question = Questions.objects.create(
            test=test,
            question_type=source_question.question_type,
            question=source_question.question,
            marks=source_question.marks,
            order=next_order,
            max_words=source_question.max_words,
            min_words=source_question.min_words,
            image=source_question.image,
            image_description=source_question.image_description,
            bank_source_question=root,
            is_customized=False,
        )
        next_order += 1
        existing_root_ids.add(root.id)
        added += 1

        if source_question.question_type in ("MCQ", "TF", "MSQ"):
            QuestionOption.objects.bulk_create([
                QuestionOption(
                    question=new_question,
                    option_text=opt.option_text,
                    is_correct=opt.is_correct
                )
                for opt in source_question.options.all()
            ])

        if source_question.question_type == "MTF":
            item_map = {}
            for item in source_question.match_items.all():
                item_map[item.id] = MatchItem.objects.create(
                    question=new_question,
                    column=item.column,
                    label=item.label,
                    order=item.order
                )
            MatchPair.objects.bulk_create([
                MatchPair(
                    question=new_question,
                    item_a=item_map[pair.item_a_id],
                    item_b=item_map[pair.item_b_id]
                )
                for pair in source_question.match_pairs.all()
            ])

    return JsonResponse({'success': True, 'added': added})

@teacher_required
def question_detail(request, pk, pk2):
    q = get_object_or_404(Questions, pk=pk2)

    options_arr = {}
    match_item = {}
    if q.question_type == "MCQ" or q.question_type == "TF" or q.question_type == "MSQ":
        opt = q.options.all()
        for o in opt:
            options_arr[ o.id] = o.option_text, o.is_correct

    if q.question_type == "MTF":
        items = q.match_pairs.all()
        for item in items:
            match_item[item.id] = item.item_a.id, item.item_a.label, item.item_b.id, item.item_b.label

    if q.image:
        image_url = q.image.name
    else:
        image_url = None

    data = {
        'id': q.id,
        'question_type': q.question_type,
        'question': q.question,
        'marks': q.marks,
        'order': q.order,
        'max_words': q.max_words,
        'min_words': q.min_words,
        'options': json.dumps(options_arr),
        'image' : image_url,
        'image_description' : q.image_description,
        'match_items': json.dumps(match_item),
        'is_shuffled': q.is_shuffled,
        }
    return JsonResponse(data)

@teacher_required
def bank_question_detail(request, pk, pk2):
    """
    Detail endpoint for Question Bank preview inside a test flow.
    Ensures the question belongs to the same institute and matches test standard/subject.
    """
    test = get_object_or_404(Tests, pk=pk, user=request.user)
    q = get_object_or_404(
        Questions.objects.select_related('test', 'test__user').prefetch_related(
            'options',
            'match_pairs__item_a',
            'match_pairs__item_b',
        ),
        pk=pk2
    )

    # Safety checks
    if q.test.user.institute != request.user.institute:
        return HttpResponseBadRequest("Invalid question")
    if q.test.standard != test.standard or q.test.subject != test.subject:
        return HttpResponseBadRequest("Invalid question")
    if q.test_id == test.id:
        return HttpResponseBadRequest("Invalid question")

    options = []
    if q.question_type in ("MCQ", "TF", "MSQ"):
        options = [{'text': o.option_text, 'is_correct': bool(o.is_correct)} for o in q.options.all()]

    pairs = []
    if q.question_type == "MTF":
        pairs = [{'a': p.item_a.label, 'b': p.item_b.label} for p in q.match_pairs.all()]

    return render(request, "bank_question_preview.html", {
        "question": q,
        "options": options,
        "pairs": pairs,
    })

@teacher_required
@transaction.atomic
@require_http_methods(["POST"])
def question_create(request, pk):
    form = QuestionsForm(request.POST, request.FILES)

    if form.is_valid():
        question = form.save(commit=False)
        question.test = get_object_or_404(Tests, pk=pk)    
        question.save()
        
        # to create the options of mcq and true/false
        if(question.question_type == "MCQ" or question.question_type == "TF"):
            options = request.POST.getlist('options[]')
            correct_index = int(request.POST.get('correct_option', -1))
        
            for i, option_text in enumerate(options, start=1):
                # print("test", option_text, correct_index)
                QuestionOption.objects.create(
                    question=question,
                    option_text=option_text,
                    is_correct=(i == correct_index)
                )

        if(question.question_type == "MSQ"):
            options = request.POST.getlist('options[]')
            correct_option_ids = request.POST.getlist('correct_options[]', [-1])
        
            for i, option_text in enumerate(options, start=1):

                isCorrect = False
                for correct_option_id in correct_option_ids:
                    if (i == int(correct_option_id)):
                        isCorrect = True
                        break 
                
                QuestionOption.objects.create(
                    question = question,
                    option_text = option_text,
                    is_correct = isCorrect
                )

        if(question.question_type == "MTF"):
            col_a = request.POST.getlist('mulitple_choice_col_A[]')
            col_b = request.POST.getlist('mulitple_choice_col_B[]')

            if len(col_a) != len(col_b):
                raise ValueError("Column A and B must have same number of items")

            items_a = []
            items_b = []
            for idx, text in enumerate(col_a):
                items_a.append(MatchItem(question=question, column='A', label=text.strip(), order=idx))
            for idx, text in enumerate(col_b):
                items_b.append(MatchItem(question=question, column='B', label=text.strip(), order=idx))

            MatchItem.objects.bulk_create(items_a + items_b)

            # After bulk_create, need to fetch created items (bulk_create doesn't set PKs reliably across DBs)
            # Fetch by question and column & order
            created_a = list(MatchItem.objects.filter(question=question, column='A').order_by('order'))
            created_b = list(MatchItem.objects.filter(question=question, column='B').order_by('order'))

            # Create pairs: assume A[i] matches B[i]
            pairs = []
            for a_item, b_item in zip(created_a, created_b):
                pairs.append(MatchPair(question=question, item_a=a_item, item_b=b_item))
            MatchPair.objects.bulk_create(pairs)

        return JsonResponse({'success': True,})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@teacher_required
@transaction.atomic
@require_http_methods(["POST"])
def question_update(request, pk, pk2):
    q = get_object_or_404(Questions, pk=pk2)
    # include request.FILES so updated image uploads are handled
    form = QuestionsForm(request.POST, request.FILES, instance=q)
    if form.is_valid():
        question = form.save(commit=False)
        question.test = get_object_or_404(Tests, pk=pk)    
        question.audio_file = "" # Clear existing audio file reference on update;
        # If it originated from bank, consider it customized after any edit.
        if question.bank_source_question_id:
            question.is_customized = True
        question.save()

        if(question.question_type == "MCQ" or question.question_type == "TF"):
            # to update the options of mcq and true/false
            options = request.POST.getlist('options[]')
            option_ids = request.POST.getlist("option_ids[]")
            correct_option_id = request.POST.get("correct_option", -1)
            existing_ids = []

            for i,(text, opt_id) in enumerate(zip(options, option_ids),start=1):
                if opt_id:
                    # UPDATE existing option
                    opt = QuestionOption.objects.get(id=opt_id, question=question)
                    opt.option_text = text
                    opt.is_correct = (str(opt.id) == correct_option_id)
                    opt.save()
                    existing_ids.append(opt.id)
                else:
                    # CREATE new option
                    print(i,correct_option_id)
                    opt = QuestionOption.objects.create(
                        question=question,
                        option_text=text,
                        is_correct=(i == int(correct_option_id))
                    )
                    if str(opt.id) == correct_option_id:
                        opt.is_correct = True
                        opt.save()
                    existing_ids.append(opt.id)

            # DELETE removed options
            QuestionOption.objects.filter(question=question).exclude(id__in=existing_ids).delete()

        if(question.question_type == "MSQ"):
            # to update the options of mcq and true/false
            options = request.POST.getlist('options[]')
            option_ids = request.POST.getlist("option_ids[]")
            correct_option_ids = request.POST.getlist("correct_options[]", [-1])
            print(option_ids, "correct: ", correct_option_ids)
            existing_ids = []

            for i,(text, opt_id) in enumerate(zip(options, option_ids),start=1):
                if opt_id:
                    # UPDATE existing option
                    opt = QuestionOption.objects.get(id=opt_id, question=question)
                    opt.option_text = text
                    opt.is_correct = False

                    for correct_option_id in correct_option_ids:
                        if (str(opt.id) == correct_option_id):
                            opt.is_correct = True
                            break
                            
                    opt.save()
                    existing_ids.append(opt.id)
                else:
                    # CREATE new option
                    

                    print(i,correct_option_ids)
                    opt = QuestionOption.objects.create(
                        question=question,
                        option_text=text,
                        is_correct = False,
                        )
                    
                    for correct_option_id in correct_option_ids:
                        if (i == int(correct_option_id)):
                            opt.is_correct = True
                            break

                    opt.save()
                    existing_ids.append(opt.id)

            # DELETE removed options
            QuestionOption.objects.filter(question=question).exclude(id__in=existing_ids).delete()           
        
        
        if(question.question_type == "MTF"):
            a_ids = request.POST.getlist("mulitple_choice_A_ids[]")
            a_labels = request.POST.getlist('mulitple_choice_col_A[]')
            b_ids = request.POST.getlist("mulitple_choice_B_ids[]")
            b_labels = request.POST.getlist('mulitple_choice_col_B[]')

            # Basic validation — ensure lists align
            if not (len(a_ids) == len(a_labels) and len(b_ids) == len(b_labels) and len(a_labels) == len(b_labels)):
                return HttpResponseBadRequest("List lengths must match")
            
            created_or_updated_a = []
            created_or_updated_b = []

            # Process column A
            for idx, (raw_id, label) in enumerate(zip(a_ids, a_labels)):
                label = (label or "").strip()
                if raw_id and raw_id != "0":
                    # update existing
                    try:
                        item = MatchItem.objects.get(pk=int(raw_id), question=q, column='A')
                    except MatchItem.DoesNotExist:
                        return HttpResponseBadRequest(f"Invalid A id: {raw_id}")
                    item.label = label
                    item.order = idx
                    item.save()
                else:
                    item = MatchItem.objects.create(question=q, column='A', label=label, order=idx)
                created_or_updated_a.append(item)

            # Process column B
            for idx, (raw_id, label) in enumerate(zip(b_ids, b_labels)):
                label = (label or "").strip()
                if raw_id and raw_id != "0":
                    try:
                        item = MatchItem.objects.get(pk=int(raw_id), question=q, column='B')
                    except MatchItem.DoesNotExist:
                        return HttpResponseBadRequest(f"Invalid B id: {raw_id}")
                    item.label = label
                    item.order = idx
                    item.save()
                else:
                    item = MatchItem.objects.create(question=q, column='B', label=label, order=idx)
                created_or_updated_b.append(item)

            # Rebuild pairs to match by index (delete existing pairs for this question first)
            MatchPair.objects.filter(question=q).delete()
            pairs = []
            for a_item, b_item in zip(created_or_updated_a, created_or_updated_b):
                pairs.append(MatchPair(question=q, item_a=a_item, item_b=b_item))
            MatchPair.objects.bulk_create(pairs)

            # Optionally remove any orphaned MatchItems that were deleted client-side:
            # collect client-sent ids (excluding "0"/empty) and remove non-listed items
            sent_a_int_ids = {int(x) for x in a_ids if x and x != "0"}
            sent_b_int_ids = {int(x) for x in b_ids if x and x != "0"}
            MatchItem.objects.filter(question=q, column='A').exclude(pk__in=sent_a_int_ids).exclude(pk__in=[i.pk for i in created_or_updated_a if i.pk]).delete()
            MatchItem.objects.filter(question=q, column='B').exclude(pk__in=sent_b_int_ids).exclude(pk__in=[i.pk for i in created_or_updated_b if i.pk]).delete()

        return JsonResponse({'success': True, })   
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@teacher_required
@require_http_methods(["POST"])
def question_delete(request, pk, pk2):
    q = get_object_or_404(Questions, pk=pk2)
    q.delete()
    return JsonResponse({'success': True, 'id': pk})

@teacher_required
def test_preview(request, pk):
    test = get_object_or_404(Tests, pk=pk)
    questions = test.questions.all()
    return render(request, 'test_preview.html', {'test': test, 'questions': questions})

@teacher_required
def student_list_view(request):

    base_users = CustomUser.objects.filter(institute=request.user.institute, account_type='student')
    standards = sorted(set(base_users.values_list('standard', flat=True).exclude(standard__isnull=True)))

    selected_standard_raw = request.GET.get('standard') or ''
    selected_standard = None

    if selected_standard_raw:
        try:
            selected_standard = int(selected_standard_raw)
        except (TypeError, ValueError):
            selected_standard = None
            selected_standard_raw = ''

    students = []
    if selected_standard is not None:
        students = base_users.filter(
                standard=selected_standard
            ).order_by('first_name')

    return render(request, 'student_list.html', {
        'standards': standards,
        'selected_standard': selected_standard_raw,
        'students': students,
    })


def exam_sse(request):
    institute = request.user.institute
    standard = request.user.standard

    def event_stream():
        # Only listen for events created after student connected
        last_check = datetime.datetime.now()

        while True:
            time.sleep(3)  # poll every 3 seconds
            
            event = TestEvent.objects.filter(
                institute=institute,
                standard=standard,
                created_at__gt=last_check
            ).order_by('created_at').last()

            if event:
                last_check = event.created_at
                yield f"data: {event.message}\n\n"
            else:
                yield ": heartbeat\n\n"

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

@csrf_exempt
@teacher_required
@require_POST 
def test_toggle(request):
    try:
        data = json.loads(request.body)
        test_id = data.get('test_id')
        isActive = data.get('isActive')

        if isActive is None or isActive == '':
            return JsonResponse({'error': 'isActive required'}, status=400)

        isActive = bool(isActive)
        test = get_object_or_404(Tests, pk=test_id)
        
        # Check if test contains questions when activating
        if isActive and not test.questions.exists():
            return JsonResponse({'error': "Test doesn't contain any questions"}, status=400)
        
        # Check if there's already an active test for the same standard
        if isActive and Tests.objects.filter(
            user=test.user,
            standard=test.standard,
            isActive=True
        ).exclude(pk=test.pk).exists():
            return JsonResponse({'error': 'An active test already exists for this standard'}, status=400)
        
        test.isActive = isActive
        
        # Cancel any existing schedules
        Schedule.objects.filter(name__in=[
            f'activate-test-{test_id}',
            f'deactivate-test-{test_id}'
        ]).delete()

        if isActive:
            test.activated_at = datetime.datetime.now()
            test.schedule = None  # Clear schedule when manually activated
            test.signature = test.generate_signature()
            test.save()

            # deactivate after duration in time field
            schedule(
                'teachers.tasks.deactivate_test',
                test_id,
                schedule_type=Schedule.ONCE,
                next_run=datetime.datetime.now() + test.time,  # test.time is a timedelta
                name=f'deactivate-test-{test_id}',
            )
            broadcast(test, test.user.institute, test.standard)
        else:
            test.activated_at = None
            test.readOnly = True
            test.save()
            broadcast(test, test.user.institute, test.standard, 'deactivate')

        return JsonResponse({'success': True, 'isActive': isActive})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
 
# @teacher_required
# @csrf_exempt
# def question_bank_view(request):

#     standards, selected_standard, selected_standard_raw, available_subjects, selected_subject, base_tests = get_standard_and_test(request)
#     questions = []
#     if selected_standard is not None and selected_subject:
#         tests = base_tests.filter(
#             standard__standard=selected_standard,
#             subject__name=selected_subject,
#         )
#         questions = list(
#             Questions.objects.filter(test__in=tests)
#             .select_related('test')
#             .prefetch_related('options', 'match_pairs__item_a', 'match_pairs__item_b')
#             .order_by('test__name', 'order')
#         )

#     return render(request, 'question_bank.html', {
#         'standards': standards,
#         'available_subjects': available_subjects,
#         'selected_standard': selected_standard_raw,
#         'selected_subject': selected_subject,
#         'questions': questions,
#     })


@teacher_required
def question_bank_view(request):
    standards, selected_standard_raw, selected_subject_id, selected_subject_name, tests = get_standard_and_test(request)

    questions = []
    if selected_subject_id:
         
        questions = list(
            Questions.objects.filter(test__in=tests)
            .select_related('test')
            .prefetch_related('options', 'match_pairs__item_a', 'match_pairs__item_b')
            .order_by('test__name', 'order')
        )

    # standards, selected_standard, selected_standard_raw, available_subjects, selected_subject, base_tests = get_standard_and_test(request)
    # if selected_standard is not None and selected_subject:
    #     tests = base_tests.filter(
    #         standard__standard=selected_standard,
    #         subject__name=selected_subject,
    #     )
    #     questions = list(
    #         Questions.objects.filter(test__in=tests)
    #         .select_related('test')
    #         .prefetch_related('options', 'match_pairs__item_a', 'match_pairs__item_b')
    #         .order_by('test__name', 'order')
    #     )

    return render(request, 'question_bank.html', {
        'standards': standards,
        'selected_standard': selected_standard_raw,
        'selected_subject_id': selected_subject_id,
        'selected_subject_name': selected_subject_name,
        'questions': questions,
    })

def _swap_order(q1, q2):
    q1.order, q2.order = q2.order, q1.order
    q1.audio_file = None
    q2.audio_file = None
    q1.save(update_fields=['order', 'audio_file'])
    q2.save(update_fields=['order', 'audio_file'])

@transaction.atomic
def move_question_up(request, pk):
    q = get_object_or_404(Questions, pk=pk)
    prev_q = Questions.objects.filter(test=q.test, order__lt=q.order).order_by('-order').first()
    if prev_q:
        _swap_order(q, prev_q)
    # Redirect back to same page (use Referer or fallback)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@transaction.atomic
def move_question_down(request, pk):
    q = get_object_or_404(Questions, pk=pk)
    next_q = Questions.objects.filter(test=q.test, order__gt=q.order).order_by('order').first()
    if next_q:
        _swap_order(q, next_q)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@teacher_required
@require_http_methods(["POST"])
def save_speech_models(request, pk):
    """API endpoint to save TTS and ASR model selections for a test."""
    test = get_object_or_404(Tests, pk=pk, user=request.user)
    
    tts_model = request.POST.get('tts_model', '').strip()
    asr_model = request.POST.get('asr_model', '').strip()
    
    # Update only non-empty values
    if tts_model:
        test.tts_model = tts_model
    if asr_model:
        test.asr_model = asr_model
    
    test.save(update_fields=['tts_model', 'asr_model'] if (tts_model or asr_model) else [])
    
    return JsonResponse({
        'success': True,
        'tts_model': test.tts_model,
        'asr_model': test.asr_model
    })


@login_required
@require_GET
def get_image_file(request, file_name):
    # build paths
    path_to_file = os.path.join(os.path.join(default_storage.location, file_name))

    if os.path.exists(path_to_file) and os.path.isfile(path_to_file):
        # streams file efficiently; as_attachment=False serves inline
        return FileResponse(open(path_to_file, "rb"), content_type="image/jpeg")
    else:
        return JsonResponse({"success": False, "error": "file not found!"}, status=200)


def question_audio(request, pk):
    try:
        question_id = request.POST.get('question_id')
        file_name = request.POST.get('audio_file_name')

        question = get_object_or_404(Questions, pk=question_id, test_id=pk)
        question.audio_file = file_name
        question.save(update_fields=['audio_file'])

        return JsonResponse({"success": True}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

@login_required
@require_POST
def upload_question_paper(request, test_id):
    form = QuestionPaperUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    upload = form.save(commit=False)
    upload.user = request.user
    test = get_object_or_404(Tests, pk=test_id, user=request.user)
    upload.test = test
    upload.save()

    medium = test.medium
    try:
        text = extract_text_from_file(upload.file.path, medium=medium)
        # remove special symbols and extra whitespace
        # disallowed_chars_re = regex.compile(r'[^\w.,?:\- \n\p{Mn}\p{Mc}]', regex.UNICODE)
        # text = disallowed_chars_re.sub('', text)
      
        upload.extracted_text = text
        upload.save(update_fields=['extracted_text'])
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=500)

    return JsonResponse({'success': True, 'text': text, 'upload_id': upload.id})

@login_required
@require_POST
def save_question_paper_text(request, test_id):
    
    text = request.POST.get('text', '').strip()
    # print(test_id,text)

    upload = QuestionPaperUpload.objects.filter(test_id=test_id, user=request.user).order_by('-uploaded_at').first()

    if not text:
        return JsonResponse({'success': False, 'error': 'Text cannot be empty'}, status=400)

    upload.extracted_text = text
    upload.save(update_fields=['extracted_text'])
    return JsonResponse({'success': True, 'text': text})

@login_required
@require_GET
def get_user_manual(request):
    # build paths
    path_to_file = os.path.join(os.path.join(default_storage.location, 'product', 'Sahayak_Writer_User_Manual.pdf'))

    if os.path.exists(path_to_file) and os.path.isfile(path_to_file):
        return FileResponse(open(path_to_file, "rb"), content_type="application/pdf", filename="Sahayak_Writer_User_Manual.pdf")
    else:
        return render(request, "404.html")


@login_required
@require_POST
def parse_questions_ai_view(request, pk):
    text = request.POST.get('text', '').strip()
    medium = request.POST.get('medium', 'en')

    if not text:
        return JsonResponse({'success': False, 'errors': 'No text provided'}, status=400)
        

    try:
        questions = parse_questions_with_ai(text, medium)
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'errors': 'AI response was not valid JSON — try again or shorten the selection'},
            status=502
        )
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=500)

    return JsonResponse({'success': True, 'questions': questions})


import json
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

@teacher_required
@transaction.atomic
@require_POST
def bulk_create_questions_ai(request, pk):
    test = get_object_or_404(Tests, pk=pk, user=request.user)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'errors': 'Invalid JSON body'}, status=400)

    ai_questions = payload.get('questions', [])
    if not ai_questions:
        return JsonResponse({'success': False, 'errors': 'No questions provided'}, status=400)

    valid_types = {'SA', 'LA', 'MCQ', 'TF', 'FIB', 'MTF', 'MSQ'}
    next_order = (test.questions.aggregate(m=Max('order')).get('m') or 0) + 1
    added = 0
    skipped = []

    for i, q in enumerate(ai_questions):
        q_type = q.get('question_type')
        q_text = (q.get('question_text') or '').strip()

        if q_type not in valid_types or not q_text:
            skipped.append(f"Question {i + 1}: missing/invalid type or text")
            continue

        try:
            marks = int(q.get('marks') or 1)
        except (TypeError, ValueError):
            marks = 1

        new_question = Questions.objects.create(
            test=test,
            question_type=q_type,
            question=q_text,
            marks=marks,
            order=next_order,
            is_customized=True,  # originally-authored via AI parse, not a bank copy
        )
        next_order += 1
        added += 1

        if q_type in ("MCQ", "TF", "MSQ"):
            options = [
                QuestionOption(
                    question=new_question,
                    option_text=(opt.get('text') or '').strip(),
                    is_correct=False,
                )
                for opt in (q.get('options') or [])
                if (opt.get('text') or '').strip()
            ]
            QuestionOption.objects.bulk_create(options)

        if q_type == "MTF":
            for order_idx, pair in enumerate(q.get('match_pairs') or [], start=1):
                a_label = (pair.get('a') or '').strip()
                b_label = (pair.get('b') or '').strip()
                if not a_label or not b_label:
                    continue
                item_a = MatchItem.objects.create(
                    question=new_question, column='A', label=a_label, order=order_idx
                )
                item_b = MatchItem.objects.create(
                    question=new_question, column='B', label=b_label, order=order_idx
                )
                MatchPair.objects.create(
                    question=new_question, item_a=item_a, item_b=item_b
                )

    return JsonResponse({'success': True, 'added': added, 'skipped': skipped})