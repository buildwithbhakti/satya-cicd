from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("register_institute/", views.register_institute_view, name="register_institute"),
    path("login/", views.login_view, name="login"),

    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_edit, name="profile_edit"),
    path("profile/<int:student_id>/", views.profile_edit_student, name="profile_edit_student"),

    path('profile/<int:student_id>/delete/', views.profile_delete, name='profile_delete'),

    path('student_toggle/', views.student_toggle, name='student_toggle'),

    path("password_change/", views.change_password_view , name="password_change"),
    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="password_change_done.html"), name="password_change_done"),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),

]
