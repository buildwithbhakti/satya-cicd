"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.i18n import JavaScriptCatalog

admin.site.site_header = "सहायक Writer Admin"
admin.site.site_title = "सहायक Writer Admin Portal"
admin.site.index_title = "Administration"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("brochure/", views.get_brochure_file, name="get_brochure_file"),
    path("demo_video/", views.get_demo_video, name="get_demo_video"),
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    # path("", include("home.urls")),
    path("teachers/", include("teachers.urls")),
    path("students/", include("students.urls")),
    path("speech/", include("speech.urls")),
    path("evaluate/", include("evaluate.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    # path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

