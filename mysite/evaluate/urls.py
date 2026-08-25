from django.urls import path
from . import views

urlpatterns = [
    path("tests", views.evaluate_test_list_view, name="evaluate_test_list"),
    
    path('test/students/<int:test_id>', views.students_list_evaluate, name='students_list_evaluate'),
    path('test/evaluate/<int:test_id>/<int:student_id>/<int:attempt_id>/', views.student_evaluate, name='student_evaluate'),
    path('test/retake/<int:test_id>/<int:student_id>/<int:attempt_id>/', views.student_retake, name='student_retake'),
    path('test/retake/pactice/<int:test_id>/<int:student_id>/<int:attempt_id>/', views.student_practice_retake, name='student_practice_retake'),
    
    path('save-marks/', views.save_marks, name='save_marks'),
    path('save-result/', views.save_result, name='save_result'),
    path('view-result/<int:test_id>/<int:student_id>/<int:attempt_id>/', views.view_student_result, name='view_student_result'),

    path('test/logs/<int:test_id>/<int:student_id>/', views.view_test_logs, name='view_test_logs'),


]

