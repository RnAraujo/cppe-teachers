from django.contrib import admin
from .models import Teacher, Contribution, PublicQueryLog

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('dni', 'last_name', 'first_name', 'registration_code', 'is_enabled')
    search_fields = ('dni', 'last_name', 'first_name', 'registration_code')
    list_filter = ('is_enabled',)

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'get_month_display', 'year', 'amount', 'receipt_number', 'payment_date')
    list_filter = ('year', 'month')
    search_fields = ('teacher__dni', 'teacher__last_name', 'receipt_number')

@admin.register(PublicQueryLog)
class PublicQueryLogAdmin(admin.ModelAdmin):
    list_display = ('dni', 'timestamp', 'found')
    list_filter = ('found', 'timestamp')
    search_fields = ('dni',)
    readonly_fields = ('dni', 'timestamp', 'found')
    ordering = ('-timestamp',)