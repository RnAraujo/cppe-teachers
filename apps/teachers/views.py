from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Teacher, Contribution
from .forms import TeacherForm, ContributionForm
from .utils import generate_receipt_pdf, generate_multiple_receipts_pdf
from datetime import date

def landing(request):
    teacher = None
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
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
            except Teacher.DoesNotExist:
                teacher = None
                messages.error(request, "Profesor no registrado en nuestra base de datos.")
        else:
            messages.error(request, "DNI inválido (debe tener 8 dígitos).")
    return render(request, 'landing.html', {'teacher': teacher})

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