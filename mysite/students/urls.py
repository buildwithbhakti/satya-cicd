from django.urls import path
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path("", views.students_menu_view, name="students_menu"),
    path("test/active_tests/", views.active_test_list_view, name="active_test_list"),
    path('test/<int:pk>/take_test/', views.take_test, name='take_test'),
    path('ajax/save-answer/', views.save_answer_ajax, name='save_answer_ajax'),
    path("test/submitted_tests/", views.submitted_test_list_view, name="submitted_test_list"),

    path("beacon/log-activity/", views.log_activity_batch, name="log_activity"),

    path("practice_test/", views.practice_test_view, name="practice_test"),
    path("check_speech/", views.check_speech_view, name="check_speech"),
    # path("test/<int:pk>/submit_test/", views.submit_test_view, name="submit_test"),
    
]
