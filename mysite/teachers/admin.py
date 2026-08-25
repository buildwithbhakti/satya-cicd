from django.contrib import admin
from .models import Standard, Subject, TestEvent, Tests, Questions, QuestionOption, MatchItem, MatchPair, QuestionPaperUpload

# Register your models here.

class TeachersTest(admin.ModelAdmin):
  list_display =  [field.name for field in Tests._meta.fields]
  def get_queryset(self, request):
    qs = super().get_queryset(request)
    if not request.user.is_superuser:
      return qs.filter(user__institute=request.user.institute)
    return qs

admin.site.register(Tests, TeachersTest)


class TeachersQuestions(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

admin.site.register(Questions, TeachersQuestions)


admin.site.register(QuestionOption)
admin.site.register(MatchItem)
admin.site.register(MatchPair)


class TestEventAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TestEvent._meta.fields]
    
admin.site.register(TestEvent, TestEventAdmin)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ['standard','institute', 'created_at']
    search_fields = ['standard']
    ordering = ['standard']
    filter_horizontal = ('subjects',) 
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_staff and not request.user.is_superuser:
            return qs.filter(institute=request.user.institute)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.is_staff and not request.user.is_superuser:
            if 'institute' in form.base_fields:
                institute_field = form.base_fields['institute']
                institute_field.initial = request.user.institute
                institute_field.disabled = True
        return form

    def save_model(self, request, obj, form, change):
        if request.user.is_staff and not request.user.is_superuser:
            obj.institute = request.user.institute
        super().save_model(request, obj, form, change)


admin.site.register(QuestionPaperUpload)