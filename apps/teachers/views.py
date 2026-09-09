from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Teacher, Contribution, PublicQueryLog
from .forms import TeacherForm, ContributionForm
from .utils import generate_receipt_pdf, generate_multiple_receipts_pdf, generate_vigency_certificate_pdf
from datetime import date
import calendar

def download_vigency_certificate(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    # Verificar que esté habilitado y vigente (opcional)
    last_contribution = teacher.contributions.order_by('-payment_date').first()
    if not last_contribution:
        messages.error(request, "El profesor no tiene aportes, no se puede emitir certificado.")
        return redirect('landing')
    last_day = calendar.monthrange(last_contribution.year, last_contribution.month)[1]
    last_date = date(last_contribution.year, last_contribution.month, last_day)
    today = date.today()
    if today > last_date:
        messages.error(request, "El profesor no está vigente, no se puede emitir certificado.")
        return redirect('landing')
    # Generar PDF
    pdf = generate_vigency_certificate_pdf(teacher)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificado_vigencia_{teacher.dni}.pdf"'
    return response

def landing(request):
    teacher = None
    last_teachers = Teacher.objects.all().order_by('-created_at')[:6]

    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        found = False
        if dni.isdigit() and len(dni) == 8:
            try:
                teacher = Teacher.objects.get(dni=dni)
                current_year = date.today().year
                contributions = teacher.contributions.filter(year=current_year)
                months_paid = [c.month for c in contributions]
                all_months = set(range(1, 13))
                missing = sorted(all_months - set(months_paid))
                if missing:
                    teacher.status = f"Adeuda meses: {', '.join([str(m) for m in missing])}"
                else:
                    teacher.status = "Aportes al día"

                # Cálculo de vigencia
                last_contribution = teacher.contributions.order_by('-payment_date').first()
                if last_contribution:
                    last_day = calendar.monthrange(last_contribution.year, last_contribution.month)[1]
                    last_date = date(last_contribution.year, last_contribution.month, last_day)
                    today = date.today()
                    if today <= last_date:
                        days_left = (last_date - today).days
                        teacher.vigency_status = f"Vigente por {days_left} días más"
                        teacher.vigency_class = "text-green-600"
                        teacher.is_vigent = True
                    else:
                        days_overdue = (today - last_date).days
                        teacher.vigency_status = f"Vigencia expirada (hace {days_overdue} días)"
                        teacher.vigency_class = "text-red-600"
                        teacher.is_vigent = False
                else:
                    teacher.vigency_status = "Sin aportes registrados"
                    teacher.vigency_class = "text-gray-500"
                    teacher.is_vigent = False

                found = True
            except Teacher.DoesNotExist:
                teacher = None
                messages.error(request, "Profesor no registrado en nuestra base de datos.")
        else:
            messages.error(request, "DNI inválido (debe tener 8 dígitos).")

        PublicQueryLog.objects.create(
            dni=dni,
            found=found
        )

    return render(request, 'landing.html', {
        'teacher': teacher,
        'last_teachers': last_teachers,
    })


@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    teachers_list = Teacher.objects.all().order_by('last_name')
    if query:
        teachers_list = teachers_list.filter(
            Q(dni__icontains=query) |
            Q(last_name__icontains=query) |
            Q(first_name__icontains=query) |
            Q(registration_code__icontains=query)
        )
    paginator = Paginator(teachers_list, 16)
    page = request.GET.get('page')
    try:
        teachers = paginator.page(page)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)

    # Últimos 10 profesores actualizados (independientemente de la búsqueda)
    recent_teachers = Teacher.objects.all().order_by('-updated_at')[:7]

    context = {
        'teachers': teachers,
        'query': query,
        'recent_teachers': recent_teachers,
        'total_teachers': Teacher.objects.count(),
        'enabled_count': Teacher.objects.filter(is_enabled=True).count(),
        'disabled_count': Teacher.objects.filter(is_enabled=False).count(),
    }
    return render(request, 'dashboard.html', context)

@login_required
def add_teacher(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Profesor registrado exitosamente.")
            return redirect('dashboard')
    else:
        form = TeacherForm()
    return render(request, 'add_teacher.html', {'form': form})

@login_required
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Profesor actualizado exitosamente.")
            return redirect('dashboard')
    else:
        form = TeacherForm(instance=teacher)
    return render(request, 'edit_teacher.html', {'form': form, 'teacher': teacher})

@login_required
def teacher_contributions(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    contributions = teacher.contributions.all().order_by('-year', '-month')
    return render(request, 'teacher_contributions.html', {'teacher': teacher, 'contributions': contributions})

@login_required
def add_contribution(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.teacher = teacher
            contribution.amount = 5.00
            try:
                contribution.save()
                messages.success(request, f"Aporte registrado correctamente. Comprobante: {contribution.receipt_number}")
                return redirect('teacher_contributions', teacher_id=teacher.id)
            except Exception as e:
                messages.error(request, f"Error: {str(e)} (posible duplicado de mes/año)")
                return redirect('teacher_contributions', teacher_id=teacher.id)
    else:
        form = ContributionForm(initial={'year': date.today().year})
    return render(request, 'add_contribution.html', {'teacher': teacher, 'form': form})

@login_required
def download_receipt(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    pdf = generate_receipt_pdf(contribution)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{contribution.receipt_number}.pdf"'
    return response

@login_required
def download_receipts(request):
    if request.method == 'POST':
        ids = request.POST.getlist('contribution_ids')
        if not ids:
            messages.error(request, "No se seleccionó ningún aporte.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        contributions = Contribution.objects.filter(id__in=ids)
        if not contributions:
            messages.error(request, "No se encontraron aportes.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        pdf = generate_multiple_receipts_pdf(contributions)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="recibos_aportes.pdf"'
        return response
    else:
        return redirect('dashboard')

@login_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    return render(request, 'teacher_detail.html', {'teacher': teacher})