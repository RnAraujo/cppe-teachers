from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Teacher, Contribution, PublicQueryLog

admin.site.empty_value_display = '---'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'dni',
        'full_name_display',
        'registration_code',
        'is_enabled_badge',
        'contributions_count',
    )
    list_display_links = ('dni',)
    search_fields = ('dni', 'last_name', 'first_name', 'registration_code')
    list_filter = ('is_enabled', 'created_at')
    list_per_page = 50
    ordering = ('last_name', 'first_name')
    readonly_fields = ('created_at', 'updated_at', 'photo_preview')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('dni', 'first_name', 'last_name', 'photo', 'photo_preview')
        }),
        ('Información Profesional', {
            'fields': ('registration_code', 'is_enabled')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Nombres y Apellidos', ordering='last_name')
    def full_name_display(self, obj):
        return obj.full_name()

    @admin.display(boolean=True, description='Estado', ordering='is_enabled')
    def is_enabled_badge(self, obj):
        return bool(obj.is_enabled)

    @admin.display(description='Aportes')
    def contributions_count(self, obj):
        count = obj.contributions.count()
        color = '#28a745' if count > 0 else "#5dafd4"
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:6px">{}</span>',
            color, str(count).zfill(4)
        )

    @admin.display(description='Vista Previa')
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width:200px;max-height:200px;border-radius:8px;" />',
                obj.photo.url
            )
        return 'Sin foto'


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = (
        'receipt_number',
        'formatted_amount',
        'teacher_dni',
        'teacher_fullname',
        'payment_date_display',
    )
    list_display_links = ('receipt_number',)
    list_filter = ('year', 'month', 'payment_date')
    search_fields = ('teacher__dni', 'teacher__last_name', 'teacher__first_name', 'receipt_number')
    list_per_page = 50
    list_select_related = ('teacher',)
    ordering = ('-year', '-month', '-payment_date')
    readonly_fields = ('receipt_number', 'payment_date')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Información del Aporte', {
            'fields': ('teacher', 'month', 'year', 'amount')
        }),
        ('Comprobante', {
            'fields': ('receipt_number', 'payment_date')
        }),
        ('Observaciones', {
            'fields': ('comments', 'observations'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='DNI', ordering='teacher__dni')
    def teacher_dni(self, obj):
        return obj.teacher.dni

    @admin.display(description='Nombre Completo', ordering='teacher__last_name')
    def teacher_fullname(self, obj):
        return obj.teacher.full_name()

    @admin.display(description='Monto', ordering='amount')
    def formatted_amount(self, obj):
        return format_html(
            '<span style="font-weight:bold;color:#28a745;">S/ {}</span>',
            obj.amount
        )

    @admin.display(description='Fecha de Pago', ordering='payment_date')
    def payment_date_display(self, obj):
        return obj.payment_date.strftime('%d/%m/%Y %H:%M')


@admin.register(PublicQueryLog)
class PublicQueryLogAdmin(admin.ModelAdmin):
    list_display = (
        'dni',
        'timestamp_formatted',
        'found_badge',
        'time_ago',
    )
    list_display_links = ('dni',)
    list_per_page = 25
    show_full_result_count = False
    list_filter = ('found', 'timestamp')
    search_fields = ('dni',)
    readonly_fields = ('dni', 'timestamp', 'found')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    @admin.display(description='Fecha y Hora', ordering='timestamp')
    def timestamp_formatted(self, obj):
        return obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')

    # 👇 CORRECCIÓN: Usar boolean=True correctamente
    @admin.display(boolean=True, description='¿Encontrado?', ordering='found')
    def found_badge(self, obj):
        return bool(obj.found)

    @admin.display(description='Hace')
    def time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp, now=timezone.now())