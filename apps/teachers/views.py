from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from .models import Teacher, Contribution
from .forms import TeacherForm, ContributionForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import generate_receipt_pdf

# Landing page (pública)
def landing(request):
    teacher = None
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        if dni.isdigit() and len(dni)==8:
            try:
                teacher = Teacher.objects.get(dni=dni)
                # Estado de aportes actual
                from datetime import date
                current_year = date.today().year
                contributions = teacher.contributions.filter(year=current_year)
                months_paid = [c.month for c in contributions]
                all_months = set(range(1,13))
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
def add_contribution(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.teacher = teacher
            contribution.amount = 5.00  # fijo
            try:
                contribution.save()
                messages.success(request, f"Aporte registrado correctamente. Comprobante: {contribution.receipt_number}")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error: {str(e)} (posible duplicado de mes/año)")
                return redirect('dashboard')
    else:
        form = ContributionForm(initial={'year': 2025})  # año por defecto
    return render(request, 'add_contribution.html', {'teacher': teacher, 'form': form})

@login_required
def download_receipt(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    pdf = generate_receipt_pdf(contribution)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{contribution.receipt_number}.pdf"'
    return response

@login_required
def dashboard(request):
    teachers_list = Teacher.objects.all().order_by('last_name')
    paginator = Paginator(teachers_list, 20)  # 20 por página
    page = request.GET.get('page')
    try:
        teachers = paginator.page(page)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)
    return render(request, 'dashboard.html', {'teachers': teachers})


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

# Vista para descargar recibo (ya existe, pero la agregamos por si acaso)
@login_required
def download_receipt(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    pdf = generate_receipt_pdf(contribution)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_{contribution.receipt_number}.pdf"'
    return response