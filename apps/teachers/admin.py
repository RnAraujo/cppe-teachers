from django.contrib import admin
from .models import Teacher, Contribution

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('dni', 'last_name', 'first_name', 'registration_code', 'is_enabled')
    search_fields = ('dni', 'last_name', 'first_name', 'registration_code')

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'get_month_display', 'year', 'amount', 'receipt_number')
    list_filter = ('year', 'month')