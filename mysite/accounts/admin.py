from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Institute, PasswordHistory, PasswordResetOTP

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("account_type","gender","phone","city","address","standard","institute","exam_mode")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("account_type","gender","phone","city","address","standard","institute","exam_mode")}),
    )

    def get_fieldsets(self, request, obj=None):
        if request.user.is_staff and not request.user.is_superuser:
            # For staff users, only show username and is_active
            return (
                (None, {'fields': ('username', 'is_active')}),
            )
        return super().get_fieldsets(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_staff and not request.user.is_superuser:
            return qs.filter(institute=request.user.institute)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.is_staff and not request.user.is_superuser:
            # Make all fields readonly except is_active
            readonly_fields = [field for field in form.base_fields if field != 'is_active']
            for field_name in readonly_fields:
                if field_name in form.base_fields:
                    form.base_fields[field_name].disabled = True
        return form

    def has_add_permission(self, request):
        if request.user.is_staff and not request.user.is_superuser:
            return False
        return super().has_add_permission(request)

    def save_model(self, request, obj, form, change):
        if request.user.is_staff and not request.user.is_superuser:
            # Ensure institute is set to the staff user's institute
            obj.institute = request.user.institute
        super().save_model(request, obj, form, change)

class RegisteredInstitutes(admin.ModelAdmin):
  list_display =  [field.name for field in Institute._meta.fields]

admin.site.register(Institute, RegisteredInstitutes)

class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = [field.name for field in PasswordResetOTP._meta.fields]

admin.site.register(PasswordResetOTP, PasswordResetOTPAdmin)


admin.site.register(PasswordHistory)