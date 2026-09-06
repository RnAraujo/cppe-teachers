from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Teacher(models.Model):
    dni = models.CharField(max_length=8, unique=True, verbose_name="DNI")
    first_name = models.CharField(max_length=100, verbose_name="Nombres")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    registration_code = models.CharField(max_length=20, unique=True, verbose_name="Código de Colegiatura")
    is_enabled = models.BooleanField(default=True, verbose_name="Habilitado")
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True, verbose_name="Foto")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teachers'
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"

    def __str__(self):
        return f"{self.dni} - {self.last_name}, {self.first_name}"

    def full_name(self):
        return f"{self.last_name} {self.first_name}"

class Contribution(models.Model):
    MONTH_CHOICES = [(i, f"{i:02d}") for i in range(1, 13)]

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='contributions')
    month = models.IntegerField(choices=MONTH_CHOICES, verbose_name="Mes")
    year = models.IntegerField(validators=[MinValueValidator(2000), MaxValueValidator(2100)], verbose_name="Año")
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=5.00, verbose_name="Monto")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de pago")
    receipt_number = models.CharField(max_length=20, unique=True, editable=False, verbose_name="N° Comprobante")
    comments = models.TextField(blank=True, verbose_name="Comentarios")
    observations = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        db_table = 'contributions'
        unique_together = ('teacher', 'month', 'year')
        verbose_name = "Aporte"
        verbose_name_plural = "Aportes"
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.teacher} - {self.get_month_display()}/{self.year}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            last = Contribution.objects.all().order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.receipt_number = f"CPPE-{self.year}-{next_id:04d}"
        super().save(*args, **kwargs)