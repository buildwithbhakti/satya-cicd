from django.contrib import admin
from .models import Answers, Attempts, MatchedPair, SelectedOption, TestLogs
# Register your models here.

class StudentsAnswers(admin.ModelAdmin):
  def get_readonly_fields(self, request, obj=None):
    return [field.name for field in self.model._meta.fields]

admin.site.register(Answers, StudentsAnswers)

admin.site.register(MatchedPair)

admin.site.register(SelectedOption)

class StudentsAttempts(admin.ModelAdmin):
  list_display =  [field.name for field in Attempts._meta.fields]
  def get_queryset(self, request):
    qs = super().get_queryset(request)
    if not request.user.is_superuser:
      return qs.filter(user__institute=request.user.institute)
    return qs
  
admin.site.register(Attempts, StudentsAttempts)

class TestLogsAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TestLogs._meta.fields]  

admin.site.register(TestLogs, TestLogsAdmin)