from django.urls import path
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path("", views.teachers_menu_view, name="teachers_menu"),
    path('test/tests/', views.test_list, name='test_list'),
    # path('test/tests/active', views.test_list_active, name='test_list_active'),
    path('test/tests/view/<int:test_id>/', views.test_view, name='test_view'),
    
    path('test/create/', views.test_create, name='test_create'),
    path('test/subjects-by-standard/', views.get_subjects_by_standard, name='get_subjects_by_standard'),
    path('test/<int:pk>/questions/', views.test_questions, name='test_questions'),
    path('test/<int:pk>/preview/', views.test_preview, name='test_preview'),

    path('test/<int:pk>/edit/', views.test_edit, name='test_edit'),
    path('test/<int:pk>/save_speech_models/', views.save_speech_models, name='save_speech_models'),
    path('test/<int:pk>/delete/', views.test_delete, name='test_delete'),
    
    path('test/<int:pk>/questions/create/', views.question_create, name='question_create'),
    path('test/<int:pk>/questions/audio/', views.question_audio, name='question_audio'),
    path('test/<int:pk>/questions/<int:pk2>/', views.question_detail, name='question_detail'),
    path('test/<int:pk>/questions/<int:pk2>/update/', views.question_update, name='question_update'),
    path('test/<int:pk>/questions/bank/<int:pk2>/', views.bank_question_detail, name='bank_question_detail'),

    path('test/<int:pk>/questions/<int:pk2>/delete/', views.question_delete, name='question_delete'),

    path('test_toggle/', views.test_toggle, name='test_toggle'),

    path("student_list/", views.student_list_view, name="student_list"),

    path("question_bank/", views.question_bank_view, name="question_bank"),

    path('test/<int:pk>/questions/import_from_bank/', views.question_import_from_bank, name='question_import_from_bank'),


    path('questions/<int:pk>/move_up/', views.move_question_up, name='question-move-up'),
    path('questions/<int:pk>/move_down/', views.move_question_down, name='question-move-down'),

    path('questions/get_image_file/<path:file_name>/', views.get_image_file, name='get_image_file'),

    path('test/exam-stream/', views.exam_sse, name='exam-sse'),

    path('upload-paper/<int:test_id>/', views.upload_question_paper, name='upload_question_paper'),
    path('save-paper-text/<int:test_id>/', views.save_question_paper_text, name='save_question_paper_text'),

    path('test/<int:pk>/questions/parse-ai/', views.parse_questions_ai_view, name='parse_questions_ai'),
    path('test/<int:pk>/questions/bulk-create-ai/', views.bulk_create_questions_ai, name='bulk_create_questions_ai'),

    path("user-manual/", views.get_user_manual, name="get_user_manual"),

]
